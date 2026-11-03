from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket
from app.models.user import User
from app.repositories.ticket_repository import TicketRepository
from app.repositories.unit_repository import UnitRepository
from app.schemas.ticket import TicketCreate, TicketReply, TicketResponse, TicketStatusUpdate


class TicketService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.ticket_repo = TicketRepository(db)
        self.unit_repo = UnitRepository(db)

    def _to_response(self, t: Ticket, current_user_id: int) -> TicketResponse:
        unidade_desc = f"{t.unidade.bloco} - Apto {t.unidade.numero}" if t.unidade else "Geral / Condomínio"
        morador_nome = t.usuario.nome if t.usuario else "Condômino"
        respondido_por_nome = t.sindico.nome if t.sindico else None
        return TicketResponse(
            id=t.id,
            unidade_id=t.unidade_id,
            unidade_desc=unidade_desc,
            usuario_id=t.usuario_id,
            morador_nome=morador_nome,
            titulo=t.titulo,
            descricao=t.descricao,
            categoria=t.categoria,
            status=t.status,
            resposta_sindico=t.resposta_sindico,
            respondido_por_nome=respondido_por_nome,
            respondido_em=t.respondido_em,
            is_mine=(t.usuario_id == current_user_id),
            criado_em=t.criado_em,
            atualizado_em=t.atualizado_em
        )

    async def list_tickets(self, current_user: User, status_filter: Optional[str] = None) -> List[TicketResponse]:
        """
        Retorna a lista de ocorrências:
        - Morador: vê apenas as suas ocorrências (privacidade e LGPD).
        - Síndico / Admin: vê todas as ocorrências estritamente do seu condomínio.
        """
        if current_user.tipo_usuario == "MORADOR":
            tickets = await self.ticket_repo.list_by_user(current_user.id)
            if status_filter:
                tickets = [t for t in tickets if t.status == status_filter.upper()]
        else:
            tickets = await self.ticket_repo.list_all(
                condominio_id=current_user.condominio_id,
                status_filter=status_filter
            )

        return [self._to_response(t, current_user.id) for t in tickets]

    async def create_ticket(self, current_user: User, data: TicketCreate) -> TicketResponse:
        """Abre uma nova ocorrência ou chamado no condomínio."""
        if current_user.tipo_usuario == "PORTARIA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Funcionários da portaria não abrem ocorrências de moradores."
            )

        unidade_id = data.unidade_id or current_user.unidade_id
        if unidade_id:
            unit = await self.unit_repo.get_by_id(unidade_id, condominio_id=current_user.condominio_id)
            if not unit:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Unidade informada não pertence ao seu condomínio."
                )

        from app.core.security import sanitize_text

        ticket = Ticket(
            condominio_id=current_user.condominio_id,
            unidade_id=unidade_id,
            usuario_id=current_user.id,
            titulo=sanitize_text(data.titulo),
            descricao=sanitize_text(data.descricao),
            categoria=data.categoria,
            status="ABERTO"
        )
        created = await self.ticket_repo.create(ticket)
        reloaded = await self.ticket_repo.get_by_id(created.id, condominio_id=current_user.condominio_id)
        assert reloaded is not None
        return self._to_response(reloaded, current_user.id)

    async def reply_ticket(self, current_user: User, ticket_id: int, data: TicketReply) -> TicketResponse:
        """Síndico registra o parecer administrativo e atualiza o status."""
        if current_user.tipo_usuario not in ("ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o síndico ou administração podem responder ocorrências."
            )

        ticket = await self.ticket_repo.get_by_id(ticket_id, condominio_id=current_user.condominio_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ocorrência não encontrada ou pertence a outro condomínio."
            )

        from app.core.security import sanitize_text

        ticket.resposta_sindico = sanitize_text(data.resposta_sindico)
        ticket.status = data.status
        ticket.respondido_por = current_user.id
        ticket.respondido_em = datetime.now()

        updated = await self.ticket_repo.update(ticket)
        return self._to_response(updated, current_user.id)

    async def cancel_ticket(self, current_user: User, ticket_id: int) -> TicketResponse:
        """Morador cancela uma ocorrência que ele próprio abriu."""
        ticket = await self.ticket_repo.get_by_id(ticket_id, condominio_id=current_user.condominio_id)
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ocorrência não encontrada ou pertence a outro condomínio."
            )

        if current_user.tipo_usuario == "MORADOR" and ticket.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para cancelar ocorrências de outros moradores."
            )

        if ticket.status == "CONCLUIDO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível cancelar uma ocorrência que já foi concluída e respondida pelo síndico."
            )

        ticket.status = "CANCELADO"
        updated = await self.ticket_repo.update(ticket)
        return self._to_response(updated, current_user.id)
