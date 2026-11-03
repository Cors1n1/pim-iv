from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery
from app.models.user import User
from app.repositories.delivery_repository import DeliveryRepository
from app.repositories.unit_repository import UnitRepository
from app.schemas.delivery import (
    DeliveryBatchDeliver,
    DeliveryBatchDeliverResponse,
    DeliveryCreate,
    DeliveryDeliver,
    DeliveryResponse
)


class DeliveryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.delivery_repo = DeliveryRepository(db)
        self.unit_repo = UnitRepository(db)

    async def get_deliveries_for_user(
        self,
        current_user: User,
        status_filter: Optional[str] = None
    ) -> List[DeliveryResponse]:
        """
        Retorna as encomendas com controle estrito de privacidade e perfil:
        - Morador: vê APENAS encomendas da sua própria unidade.
        - Portaria/Síndico: vê todas as encomendas estritamente do seu condomínio.
        """
        if current_user.tipo_usuario == "MORADOR":
            if not current_user.unidade_id:
                return []
            deliveries = await self.delivery_repo.list_by_unit(current_user.unidade_id, status_filter)
        else:
            deliveries = await self.delivery_repo.list_all(
                condominio_id=current_user.condominio_id,
                status=status_filter
            )

        return [DeliveryResponse.model_validate(d) for d in deliveries]

    async def register_delivery(
        self,
        current_user: User,
        data: DeliveryCreate
    ) -> DeliveryResponse:
        """Registra a chegada de uma nova encomenda na portaria."""
        if current_user.tipo_usuario not in ["ADMIN", "SINDICO", "PORTARIA"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas a portaria e a administração podem registrar encomendas."
            )

        unit = await self.unit_repo.get_by_id(data.unidade_id, condominio_id=current_user.condominio_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade de destino não encontrada ou pertence a outro condomínio."
            )

        if not unit.morador_responsavel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é possível registrar encomendas para o apartamento '{unit.bloco} - Apto {unit.numero}', pois ele está vago (sem morador cadastrado)."
            )

        new_delivery = Delivery(
            condominio_id=current_user.condominio_id,
            unidade_id=data.unidade_id,
            descricao=data.descricao.strip(),
            codigo_rastreio=data.codigo_rastreio.strip() if data.codigo_rastreio else None,
            porteiro_recebedor_id=current_user.id,
            status="AGUARDANDO_RETIRADA"
        )
        created = await self.delivery_repo.create(new_delivery)

        # Dispara notificação por e-mail para o morador de forma desacoplada
        if unit.morador_responsavel and unit.morador_responsavel.email:
            try:
                import asyncio
                from app.repositories.condominio_repository import CondominioRepository
                from app.services.email_service import EmailService
                condo = await CondominioRepository(self.db).get_by_id(current_user.condominio_id)
                condo_nome = condo.nome if condo else "Condomínio"
                unit_desc = f"{unit.bloco} - Apto {unit.numero}"
                asyncio.create_task(
                    EmailService.send_delivery_alert(
                        to_email=unit.morador_responsavel.email,
                        resident_name=unit.morador_responsavel.nome,
                        condo_nome=condo_nome,
                        unit_desc=unit_desc,
                        package_desc=created.descricao,
                        tracking_code=created.codigo_rastreio
                    )
                )
            except Exception as e:
                # Log e continua sem interromper a portaria
                pass

        reloaded = await self.delivery_repo.get_by_id(created.id, condominio_id=current_user.condominio_id)
        return DeliveryResponse.model_validate(reloaded)

    async def mark_as_delivered(
        self,
        current_user: User,
        delivery_id: int,
        data: DeliveryDeliver
    ) -> DeliveryResponse:
        """Dá baixa na entrega quando o morador retira o pacote na portaria."""
        if current_user.tipo_usuario != "PORTARIA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas funcionários da portaria podem dar baixa na retirada de encomendas."
            )

        delivery = await self.delivery_repo.get_by_id(delivery_id, condominio_id=current_user.condominio_id)
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encomenda não encontrada ou pertence a outro condomínio."
            )

        if delivery.status == "ENTREGUE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta encomenda já foi entregue anteriormente."
            )

        retirado_por = data.retirado_por.strip() if data.retirado_por else (
            delivery.unidade.morador_responsavel.nome if delivery.unidade and delivery.unidade.morador_responsavel else "Morador da unidade"
        )

        updated = await self.delivery_repo.mark_as_delivered(delivery_id, retirado_por, condominio_id=current_user.condominio_id)
        return DeliveryResponse.model_validate(updated)

    async def mark_batch_as_delivered(
        self,
        current_user: User,
        data: DeliveryBatchDeliver
    ) -> DeliveryBatchDeliverResponse:
        """Dá baixa em lote nas encomendas do morador na portaria."""
        if current_user.tipo_usuario != "PORTARIA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas funcionários da portaria podem dar baixa na retirada de encomendas."
            )

        target_ids = list(data.delivery_ids or [])

        # Se foi passado unidade_id, busca todas as encomendas pendentes daquela unidade
        if data.unidade_id:
            pending_unit_deliveries = await self.delivery_repo.list_by_unit(
                unit_id=data.unidade_id,
                status="AGUARDANDO_RETIRADA"
            )
            for d in pending_unit_deliveries:
                if d.condominio_id == current_user.condominio_id and d.id not in target_ids:
                    target_ids.append(d.id)

        if not target_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma encomenda pendente encontrada para dar baixa."
            )

        retirado_por = (data.retirado_por or "").strip()
        if not retirado_por:
            first_delivery = await self.delivery_repo.get_by_id(target_ids[0], condominio_id=current_user.condominio_id)
            if first_delivery and first_delivery.unidade and first_delivery.unidade.morador_responsavel:
                retirado_por = first_delivery.unidade.morador_responsavel.nome
            else:
                retirado_por = "Morador da unidade"

        delivered = await self.delivery_repo.mark_batch_as_delivered(
            delivery_ids=target_ids,
            retirado_por=retirado_por,
            condominio_id=current_user.condominio_id
        )

        return DeliveryBatchDeliverResponse(
            delivered_count=len(delivered),
            deliveries=[DeliveryResponse.model_validate(d) for d in delivered]
        )

    async def get_pending_count(self, current_user: User) -> int:

        """Retorna o número de encomendas aguardando retirada no condomínio."""
        unit_id = current_user.unidade_id if current_user.tipo_usuario == "MORADOR" else None
        return await self.delivery_repo.count_pending(condominio_id=current_user.condominio_id, unit_id=unit_id)
