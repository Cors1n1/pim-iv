from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.delivery import Delivery
from app.models.user import User
from app.repositories.delivery_repository import DeliveryRepository
from app.repositories.unit_repository import UnitRepository
from app.schemas.delivery import DeliveryCreate, DeliveryDeliver, DeliveryResponse


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
        - Portaria/Síndico: vê todas as encomendas do condomínio.
        """
        if current_user.tipo_usuario == "MORADOR":
            if not current_user.unidade_id:
                return []
            deliveries = await self.delivery_repo.list_by_unit(current_user.unidade_id, status_filter)
        else:
            deliveries = await self.delivery_repo.list_all(status_filter)

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

        unit = await self.unit_repo.get_by_id(data.unidade_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade de destino não encontrada."
            )

        if not unit.morador_responsavel_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é possível registrar encomendas para o apartamento '{unit.bloco} - Apto {unit.numero}', pois ele está vago (sem morador cadastrado)."
            )

        new_delivery = Delivery(
            unidade_id=data.unidade_id,
            descricao=data.descricao.strip(),
            codigo_rastreio=data.codigo_rastreio.strip() if data.codigo_rastreio else None,
            porteiro_recebedor_id=current_user.id,
            status="AGUARDANDO_RETIRADA"
        )
        created = await self.delivery_repo.create(new_delivery)
        # Recarrega com os relacionamentos
        reloaded = await self.delivery_repo.get_by_id(created.id)
        return DeliveryResponse.model_validate(reloaded)

    async def mark_as_delivered(
        self,
        current_user: User,
        delivery_id: int,
        data: DeliveryDeliver
    ) -> DeliveryResponse:
        """Dá baixa na entrega quando o morador retira o pacote na portaria."""
        if current_user.tipo_usuario not in ["ADMIN", "SINDICO", "PORTARIA"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas a portaria e administração podem dar baixa em encomendas."
            )

        delivery = await self.delivery_repo.get_by_id(delivery_id)
        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encomenda não encontrada."
            )

        if delivery.status == "ENTREGUE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta encomenda já foi entregue anteriormente."
            )

        retirado_por = data.retirado_por.strip() if data.retirado_por else (
            delivery.unidade.morador_responsavel.nome if delivery.unidade and delivery.unidade.morador_responsavel else "Morador da unidade"
        )

        updated = await self.delivery_repo.mark_as_delivered(delivery_id, retirado_por)
        return DeliveryResponse.model_validate(updated)

    async def get_pending_count(self, current_user: User) -> int:
        """Retorna o número de encomendas aguardando retirada."""
        unit_id = current_user.unidade_id if current_user.tipo_usuario == "MORADOR" else None
        return await self.delivery_repo.count_pending(unit_id)
