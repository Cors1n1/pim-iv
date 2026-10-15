from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.routers.deps import get_current_user, get_db, require_role
from app.schemas.settings import (
    CondoSettingsPublicResponse,
    CondoSettingsResponse,
    CondoSettingsUpdate,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/settings", tags=["Configurações do Condomínio"])


@router.get("/public", response_model=CondoSettingsPublicResponse, summary="Obter dados públicos de identificação do condomínio")
async def get_public_condo_settings(
    db: AsyncSession = Depends(get_db)
) -> CondoSettingsPublicResponse:
    """Retorna os dados públicos institucionais (nome, endereço, contatos da portaria)."""
    service = SettingsService(db)
    return await service.get_public_settings()


@router.get("", response_model=CondoSettingsResponse, summary="Obter configurações e parâmetros do condomínio")
async def get_condo_settings(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> CondoSettingsResponse:
    """Retorna os parâmetros de governança, identidade e regras operacionais do condomínio."""
    service = SettingsService(db)
    return await service.get_admin_settings(_current_user) if _current_user.tipo_usuario in ("ADMIN", "SINDICO") else await service.repo.get_settings()


@router.put("", response_model=CondoSettingsResponse, summary="Atualizar configurações do condomínio (exclusivo síndico)")
async def update_condo_settings(
    payload: CondoSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> CondoSettingsResponse:
    """Permite ao síndico personalizar nome, endereço, contatos e parâmetros de governança do condomínio."""
    service = SettingsService(db)
    return await service.update_settings(current_user=current_user, data=payload)
