from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.notice import Notice


class NoticeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_all(self) -> List[Notice]:
        """Retorna todos os comunicados ordenados pelos mais recentes."""
        stmt = (
            select(Notice)
            .options(joinedload(Notice.autor))
            .order_by(Notice.criado_em.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, notice_id: int) -> Optional[Notice]:
        """Busca um aviso específico por ID."""
        stmt = (
            select(Notice)
            .options(joinedload(Notice.autor))
            .where(Notice.id == notice_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, notice: Notice) -> Notice:
        """Persiste um novo comunicado no banco de dados."""
        self.db.add(notice)
        await self.db.commit()
        await self.db.refresh(notice)
        return notice

    async def delete(self, notice: Notice) -> None:
        """Remove um comunicado."""
        await self.db.delete(notice)
        await self.db.commit()
