from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AccessLog


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_logs(self, condominio_id: Optional[int] = None, limit: int = 50) -> List[AccessLog]:
        """Consulta os registros de auditoria com filtro por condomínio."""
        stmt = select(AccessLog)
        if condominio_id is not None:
            stmt = stmt.where(AccessLog.condominio_id == condominio_id)
        stmt = stmt.order_by(AccessLog.data_hora.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_log(
        self,
        usuario_id: Optional[int] = None,
        condominio_id: Optional[int] = None,
        email_informado: Optional[str] = None,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None,
        sucesso: bool = True,
        acao: Optional[str] = None,
        detalhes: Optional[str] = None
    ) -> AccessLog:
        """Registra um evento de auditoria ou acesso."""
        log = AccessLog(
            condominio_id=condominio_id,
            usuario_id=usuario_id,
            email_informado=email_informado or (detalhes[:140] if detalhes else "SISTEMA"),
            ip_origem=ip_origem,
            user_agent=f"{acao}: {detalhes}" if acao else user_agent,
            sucesso=sucesso
        )
        self.db.add(log)
        await self.db.commit()
        return log
