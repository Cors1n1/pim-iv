from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db, require_role
from app.schemas.notice import NoticeCreate, NoticeResponse
from app.services.notice_service import NoticeService

router = APIRouter(prefix="/api/notices", tags=["Mural de Avisos & Comunicados"])


@router.get("", response_model=List[NoticeResponse], summary="Listar todos os comunicados oficiais")
async def list_notices(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> List[NoticeResponse]:
    """Retorna os avisos cadastrados no condomínio para todos os moradores e funcionários."""
    service = NoticeService(db)
    return await service.list_notices(current_user=_current_user)


@router.post("", response_model=NoticeResponse, status_code=status.HTTP_201_CREATED, summary="Publicar novo comunicado oficial")
async def create_notice(
    payload: NoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> NoticeResponse:
    """Publica um novo aviso para todo o condomínio. Exclusivo para Síndico ou Admin."""
    service = NoticeService(db)
    return await service.create_notice(current_user, payload)


@router.delete("/{notice_id}", summary="Excluir comunicado oficial")
async def delete_notice(
    notice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> dict:
    """Remove um comunicado oficial do mural."""
    service = NoticeService(db)
    return await service.delete_notice(current_user, notice_id)
