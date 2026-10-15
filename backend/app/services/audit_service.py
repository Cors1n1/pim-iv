from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogResponse


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    async def get_recent_logs(self, limit: int = 50) -> List[AuditLogResponse]:
        """
        Retorna o histórico de logs de segurança para rastreabilidade de acessos e conformidade.
        """
        logs = await self.repo.list_logs(limit=limit)
        return [AuditLogResponse.model_validate(log) for log in logs]
