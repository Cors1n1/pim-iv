from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery import Delivery


class DeliveryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self, status: Optional[str] = None) -> List[Delivery]:
        """Lista todas as encomendas com dados da unidade vinculada."""
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.unidade))
            .order_by(Delivery.data_chegada.desc())
        )
        if status:
            stmt = stmt.where(Delivery.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_unit(self, unit_id: int, status: Optional[str] = None) -> List[Delivery]:
        """Lista apenas encomendas da unidade específica (Privacidade do Morador / LGPD)."""
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.unidade))
            .where(Delivery.unidade_id == unit_id)
            .order_by(Delivery.data_chegada.desc())
        )
        if status:
            stmt = stmt.where(Delivery.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, delivery_id: int) -> Optional[Delivery]:
        """Busca encomenda por ID."""
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.unidade))
            .where(Delivery.id == delivery_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, delivery: Delivery) -> Delivery:
        """Salva nova encomenda no banco."""
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def mark_as_delivered(self, delivery_id: int, retirado_por: str) -> Optional[Delivery]:
        """Atualiza o status para ENTREGUE com data e responsável pela retirada."""
        delivery = await self.get_by_id(delivery_id)
        if not delivery:
            return None

        delivery.status = "ENTREGUE"
        delivery.data_retirada = datetime.now(timezone.utc)
        delivery.retirado_por = retirado_por

        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def count_pending(self, unit_id: Optional[int] = None) -> int:
        """Conta encomendas aguardando retirada na portaria."""
        stmt = select(func.count(Delivery.id)).where(Delivery.status == "AGUARDANDO_RETIRADA")
        if unit_id:
            stmt = stmt.where(Delivery.unidade_id == unit_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
