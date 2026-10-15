from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db, require_role
from app.schemas.unit import AssignResidentRequest, UnitCreate, UnitResponse, UnitUpdate
from app.services.unit_service import UnitService

router = APIRouter(prefix="/api/units", tags=["Unidades & Apartamentos"])


@router.get("", response_model=List[UnitResponse], summary="Listar todas as unidades do condomínio")
async def list_units(
    include_inactive: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[UnitResponse]:
    """Retorna lista de todos os blocos e apartamentos (Apenas Administração e Portaria)."""
    if current_user.tipo_usuario == "MORADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito: Condôminos não possuem permissão para listar dados cadastrais de outros moradores (LGPD)."
        )
    service = UnitService(db)
    return await service.list_units(include_inactive=include_inactive)


@router.get("/{unit_id}", response_model=UnitResponse, summary="Obter detalhes de uma unidade")
async def get_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UnitResponse:
    """Busca os detalhes de um apartamento específico."""
    if current_user.tipo_usuario == "MORADOR" and current_user.unidade_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: Você só pode consultar os dados da sua própria unidade."
        )
    service = UnitService(db)
    return await service.get_unit(unit_id)


@router.post("", response_model=UnitResponse, summary="Cadastrar nova unidade (Síndico)")
async def create_unit(
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Permite ao síndico registrar novos apartamentos/blocos no condomínio."""
    service = UnitService(db)
    return await service.create_unit(payload)


@router.put("/{unit_id}", response_model=UnitResponse, summary="Atualizar apartamento (ativar/desativar) (Síndico)")
async def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Permite ao síndico alterar dados ou ativar/desativar uma unidade."""
    service = UnitService(db)
    return await service.update_unit(unit_id, payload)


@router.put("/{unit_id}/assign", response_model=UnitResponse, summary="Vincular morador a um apartamento (Síndico)")
async def assign_resident(
    unit_id: int,
    payload: AssignResidentRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Associa um morador cadastrado ao apartamento selecionado."""
    service = UnitService(db)
    return await service.assign_resident(unit_id, payload.morador_id)
