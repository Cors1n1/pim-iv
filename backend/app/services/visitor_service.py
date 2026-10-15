from datetime import date, datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.visitor import Visitor
from app.repositories.unit_repository import UnitRepository
from app.repositories.visitor_repository import VisitorRepository
from app.schemas.visitor import VisitorCreate, VisitorEntry, VisitorResponse


class VisitorService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.visitor_repo = VisitorRepository(db)
        self.unit_repo = UnitRepository(db)

    def _to_response(self, v: Visitor, current_user: User) -> VisitorResponse:
        unidade_desc = f"{v.unidade.bloco} - Apto {v.unidade.numero}" if v.unidade else "Unidade"
        autorizado_nome = v.morador.nome if v.morador else "Portaria"
        porteiro_in = v.porteiro_entrada.nome if v.porteiro_entrada else None
        porteiro_out = v.porteiro_saida.nome if v.porteiro_saida else None
        is_my_unit = (current_user.unidade_id == v.unidade_id) if current_user.unidade_id else False

        return VisitorResponse(
            id=v.id,
            unidade_id=v.unidade_id,
            unidade_desc=unidade_desc,
            autorizado_por_id=v.autorizado_por_id,
            autorizado_por_nome=autorizado_nome,
            nome=v.nome,
            documento=v.documento,
            tipo=v.tipo,
            data_prevista=v.data_prevista,
            status=v.status,
            hora_entrada=v.hora_entrada,
            porteiro_entrada_nome=porteiro_in,
            hora_saida=v.hora_saida,
            porteiro_saida_nome=porteiro_out,
            observacoes=v.observacoes,
            is_my_unit=is_my_unit,
            criado_em=v.criado_em,
            atualizado_em=v.atualizado_em
        )

    async def list_visitors(
        self,
        current_user: User,
        status_filter: Optional[str] = None,
        date_filter: Optional[date] = None
    ) -> List[VisitorResponse]:
        """
        Lista visitantes do condomínio:
        - Morador: vê os visitantes e prestadores vinculados à sua unidade.
        - Portaria / Síndico: vê todos os acessos do condomínio.
        """
        if current_user.tipo_usuario == "MORADOR":
            if not current_user.unidade_id:
                return []
            visitors = await self.visitor_repo.list_by_unit(current_user.unidade_id)
            if status_filter:
                visitors = [v for v in visitors if v.status == status_filter.upper()]
            if date_filter:
                visitors = [v for v in visitors if v.data_prevista == date_filter]
        else:
            visitors = await self.visitor_repo.list_all(status_filter, date_filter)

        return [self._to_response(v, current_user) for v in visitors]

    async def create_visitor(self, current_user: User, data: VisitorCreate) -> VisitorResponse:
        """Cadastra pré-autorização pelo morador ou registro direto pela portaria."""
        target_unit_id = data.unidade_id

        if current_user.tipo_usuario == "MORADOR":
            if not current_user.unidade_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Seu usuário não possui um apartamento vinculado para autorizar visitantes."
                )
            if target_unit_id is not None and target_unit_id != current_user.unidade_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você só pode autorizar visitantes para o seu próprio apartamento."
                )
            target_unit_id = current_user.unidade_id
        else:
            if not target_unit_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selecione a unidade de destino do visitante."
                )

        unit = await self.unit_repo.get_by_id(target_unit_id)
        if not unit or not unit.ativo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade de destino não encontrada ou inativa."
            )

        new_visitor = Visitor(
            unidade_id=target_unit_id,
            autorizado_por_id=current_user.id,
            nome=data.nome.strip(),
            documento=data.documento.strip() if data.documento else None,
            tipo=data.tipo,
            data_prevista=data.data_prevista,
            status="AGUARDANDO",
            observacoes=data.observacoes.strip() if data.observacoes else None
        )
        created = await self.visitor_repo.create(new_visitor)
        reloaded = await self.visitor_repo.get_by_id(created.id)
        assert reloaded is not None
        return self._to_response(reloaded, current_user)

    async def register_entry(self, current_user: User, visitor_id: int, data: Optional[VisitorEntry] = None) -> VisitorResponse:
        """Portaria registra a chegada / entrada do visitante no condomínio."""
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas funcionários da portaria ou administração podem registrar entrada de visitantes."
            )

        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de visitante não encontrado.")

        if visitor.status == "NO_LOCAL":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este visitante já consta como presente no condomínio.")

        if visitor.status == "FINALIZADO":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta visita já foi concluída anteriormente.")

        visitor.status = "NO_LOCAL"
        visitor.hora_entrada = datetime.now()
        visitor.porteiro_entrada_id = current_user.id

        if data:
            if data.documento:
                visitor.documento = data.documento.strip()
            if data.observacoes:
                visitor.observacoes = data.observacoes.strip()

        updated = await self.visitor_repo.update(visitor)
        return self._to_response(updated, current_user)

    async def register_exit(self, current_user: User, visitor_id: int) -> VisitorResponse:
        """Portaria registra a saída do visitante do condomínio."""
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas funcionários da portaria ou administração podem registrar saída de visitantes."
            )

        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de visitante não encontrado.")

        if visitor.status != "NO_LOCAL":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O visitante não consta como presente no condomínio.")

        visitor.status = "FINALIZADO"
        visitor.hora_saida = datetime.now()
        visitor.porteiro_saida_id = current_user.id

        updated = await self.visitor_repo.update(visitor)
        return self._to_response(updated, current_user)

    async def cancel_visitor(self, current_user: User, visitor_id: int) -> VisitorResponse:
        """Cancela uma autorização de visita."""
        visitor = await self.visitor_repo.get_by_id(visitor_id)
        if not visitor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro de visitante não encontrado.")

        if current_user.tipo_usuario == "MORADOR" and visitor.unidade_id != current_user.unidade_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para cancelar autorizações de outra unidade."
            )

        if visitor.status in ("NO_LOCAL", "FINALIZADO"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível cancelar uma visita que já está no local ou foi finalizada."
            )

        visitor.status = "CANCELADO"
        updated = await self.visitor_repo.update(visitor)
        return self._to_response(updated, current_user)
