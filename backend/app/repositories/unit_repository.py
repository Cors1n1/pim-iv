from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Unit, User


class UnitRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self, include_inactive: bool = True) -> List[Unit]:
        """Lista unidades com dados do morador responsável pré-carregados."""
        stmt = select(Unit).options(selectinload(Unit.morador_responsavel))
        if not include_inactive:
            stmt = stmt.where(Unit.ativo == True)
        stmt = stmt.order_by(Unit.bloco, Unit.numero)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update(self, unit: Unit) -> Unit:
        """Salva alterações em uma unidade existente."""
        await self.db.commit()
        await self.db.refresh(unit)
        return unit

    async def get_by_id(self, unit_id: int) -> Optional[Unit]:
        """Busca unidade por ID com dados do morador responsável."""
        stmt = (
            select(Unit)
            .options(selectinload(Unit.morador_responsavel))
            .where(Unit.id == unit_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_bloco_numero(self, bloco: str, numero: str) -> Optional[Unit]:
        """Busca unidade por bloco e número (únicos)."""
        stmt = select(Unit).where(Unit.bloco == bloco.strip(), Unit.numero == numero.strip())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, unit: Unit) -> Unit:
        """Cria e persiste uma nova unidade no banco."""
        self.db.add(unit)
        await self.db.commit()
        await self.db.refresh(unit)
        return unit

    async def assign_resident(self, unit_id: int, user_id: Optional[int]) -> Optional[Unit]:
        """Vincula ou desvincula um morador a uma unidade."""
        unit = await self.get_by_id(unit_id)
        if not unit:
            return None

        antigo_morador_id = unit.morador_responsavel_id
        unit.morador_responsavel_id = user_id

        if user_id:
            # Atualiza a coluna unidade_id no novo morador
            user_stmt = select(User).where(User.id == user_id)
            user_res = await self.db.execute(user_stmt)
            user = user_res.scalars().first()
            if user:
                user.unidade_id = unit_id
        elif antigo_morador_id:
            # Desvincula morador anterior
            antigo_stmt = select(User).where(User.id == antigo_morador_id)
            antigo_res = await self.db.execute(antigo_stmt)
            antigo = antigo_res.scalars().first()
            if antigo:
                antigo.unidade_id = None

        await self.db.commit()
        await self.db.refresh(unit)
        return unit
