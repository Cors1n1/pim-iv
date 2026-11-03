from datetime import date
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.visitor import Visitor


class VisitorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(
        self,
        condominio_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        date_filter: Optional[date] = None
    ) -> List[Visitor]:
        """Lista todos os visitantes e prestadores de serviço do condomínio."""
        stmt = (
            select(Visitor)
            .options(
                selectinload(Visitor.unidade),
                selectinload(Visitor.morador),
                selectinload(Visitor.porteiro_entrada),
                selectinload(Visitor.porteiro_saida)
            )
            .order_by(Visitor.data_prevista.desc(), Visitor.criado_em.desc())
        )
        if condominio_id is not None:
            stmt = stmt.where(Visitor.condominio_id == condominio_id)
        if status_filter:
            stmt = stmt.where(Visitor.status == status_filter.upper())
        if date_filter:
            stmt = stmt.where(Visitor.data_prevista == date_filter)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_unit(self, unit_id: int) -> List[Visitor]:
        """Lista visitantes e prestadores de serviço vinculados a uma unidade específica."""
        stmt = (
            select(Visitor)
            .options(
                selectinload(Visitor.unidade),
                selectinload(Visitor.morador),
                selectinload(Visitor.porteiro_entrada),
                selectinload(Visitor.porteiro_saida)
            )
            .where(Visitor.unidade_id == unit_id)
            .order_by(Visitor.data_prevista.desc(), Visitor.criado_em.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, visitor_id: int, condominio_id: Optional[int] = None) -> Optional[Visitor]:
        """Busca visitante por ID com todos os relacionamentos pré-carregados e validação de condomínio."""
        stmt = (
            select(Visitor)
            .options(
                selectinload(Visitor.unidade),
                selectinload(Visitor.morador),
                selectinload(Visitor.porteiro_entrada),
                selectinload(Visitor.porteiro_saida)
            )
            .where(Visitor.id == visitor_id)
        )
        if condominio_id is not None:
            stmt = stmt.where(Visitor.condominio_id == condominio_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, visitor: Visitor) -> Visitor:
        """Cria e persiste um novo registro de visitante ou autorização."""
        self.db.add(visitor)
        await self.db.commit()
        await self.db.refresh(visitor)
        return visitor

    async def update(self, visitor: Visitor) -> Visitor:
        """Salva alterações em um registro de visitante."""
        await self.db.commit()
        await self.db.refresh(visitor)
        return visitor
