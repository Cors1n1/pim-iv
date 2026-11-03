from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.delivery import Delivery


class DeliveryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(
        self,
        condominio_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Delivery]:
        """Lista todas as encomendas com dados da unidade vinculada e filtro por condomínio."""
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.unidade))
            .order_by(Delivery.data_chegada.desc())
        )
        if condominio_id is not None:
            stmt = stmt.where(Delivery.condominio_id == condominio_id)
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

    async def get_by_id(self, delivery_id: int, condominio_id: Optional[int] = None) -> Optional[Delivery]:
        """Busca encomenda por ID com validação de condomínio."""
        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.unidade))
            .where(Delivery.id == delivery_id)
        )
        if condominio_id is not None:
            stmt = stmt.where(Delivery.condominio_id == condominio_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, delivery: Delivery) -> Delivery:
        """Salva nova encomenda no banco."""
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def mark_as_delivered(self, delivery_id: int, retirado_por: str, condominio_id: Optional[int] = None) -> Optional[Delivery]:
        """Atualiza o status para ENTREGUE com data e responsável pela retirada."""
        delivery = await self.get_by_id(delivery_id, condominio_id=condominio_id)
        if not delivery:
            return None

        delivery.status = "ENTREGUE"
        delivery.data_retirada = datetime.now(timezone.utc)
        delivery.retirado_por = retirado_por

        await self.db.commit()
        await self.db.refresh(delivery)
        return delivery

    async def mark_batch_as_delivered(
        self,
        delivery_ids: List[int],
        retirado_por: str,
        condominio_id: Optional[int] = None
    ) -> List[Delivery]:
        """Atualiza múltiplas encomendas para ENTREGUE em uma única transação."""
        if not delivery_ids:
            return []

        stmt = (
            select(Delivery)
            .options(selectinload(Delivery.unidade))
            .where(Delivery.id.in_(delivery_ids))
        )
        if condominio_id is not None:
            stmt = stmt.where(Delivery.condominio_id == condominio_id)

        result = await self.db.execute(stmt)
        deliveries = list(result.scalars().all())

        now = datetime.now(timezone.utc)
        for d in deliveries:
            if d.status != "ENTREGUE":
                d.status = "ENTREGUE"
                d.data_retirada = now
                d.retirado_por = retirado_por

        await self.db.commit()
        for d in deliveries:
            await self.db.refresh(d)
        return deliveries


    async def count_pending(
        self,
        condominio_id: Optional[int] = None,
        unit_id: Optional[int] = None
    ) -> int:
        """Conta encomendas aguardando retirada na portaria do condomínio."""
        stmt = select(func.count(Delivery.id)).where(Delivery.status == "AGUARDANDO_RETIRADA")
        if condominio_id is not None:
            stmt = stmt.where(Delivery.condominio_id == condominio_id)
        if unit_id:
            stmt = stmt.where(Delivery.unidade_id == unit_id)
        result = await self.db.execute(stmt)
        return int(result.scalar_one())
