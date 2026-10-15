from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_db, require_role
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/audit", tags=["Auditoria & Segurança"])


@router.get("/logs", response_model=List[AuditLogResponse], summary="Listar logs de auditoria e segurança")
async def list_audit_logs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> List[AuditLogResponse]:
    """
    Retorna os registros imutáveis de acesso e autenticação para conformidade LGPD e segurança da informação.
    Exclusivo para a administração e síndico do condomínio.
    """
    service = AuditService(db)
    return await service.get_recent_logs(limit=limit)
