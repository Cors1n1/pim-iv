from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ticket import Ticket


class TicketRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(
        self,
        condominio_id: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[Ticket]:
        """Lista todas as ocorrências do condomínio com relacionamentos pré-carregados."""
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.usuario),
                selectinload(Ticket.unidade),
                selectinload(Ticket.sindico)
            )
            .order_by(Ticket.criado_em.desc())
        )
        if condominio_id is not None:
            stmt = stmt.where(Ticket.condominio_id == condominio_id)
        if status_filter:
            stmt = stmt.where(Ticket.status == status_filter.upper())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(self, user_id: int) -> List[Ticket]:
        """Lista ocorrências abertas pelo próprio morador."""
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.usuario),
                selectinload(Ticket.unidade),
                selectinload(Ticket.sindico)
            )
            .where(Ticket.usuario_id == user_id)
            .order_by(Ticket.criado_em.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, ticket_id: int, condominio_id: Optional[int] = None) -> Optional[Ticket]:
        """Busca ocorrência por ID com relacionamentos e validação de condomínio."""
        stmt = (
            select(Ticket)
            .options(
                selectinload(Ticket.usuario),
                selectinload(Ticket.unidade),
                selectinload(Ticket.sindico)
            )
            .where(Ticket.id == ticket_id)
        )
        if condominio_id is not None:
            stmt = stmt.where(Ticket.condominio_id == condominio_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, ticket: Ticket) -> Ticket:
        """Cria e persiste uma nova ocorrência."""
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def update(self, ticket: Ticket) -> Ticket:
        """Salva alterações em uma ocorrência existente."""
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket
