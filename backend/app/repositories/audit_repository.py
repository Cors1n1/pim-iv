from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AccessLog


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_logs(self, limit: int = 50) -> List[AccessLog]:
        """Consulta os registros de auditoria gravados pela Stored Procedure no PostgreSQL."""
        stmt = (
            select(AccessLog)
            .order_by(AccessLog.data_hora.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
