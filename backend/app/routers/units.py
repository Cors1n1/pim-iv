from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db, require_role
from app.schemas.unit import (
    AssignResidentRequest,
    InviteResidentRequest,
    UnitBatchCreate,
    UnitBatchResponse,
    UnitCreate,
    UnitOverviewResponse,
    UnitResponse,
    UnitUpdate
)
from app.services.unit_service import UnitService

router = APIRouter(prefix="/api/units", tags=["Unidades & Apartamentos"])


@router.get("/quick-lookup", response_model=List[UnitOverviewResponse], summary="Consulta rápida de unidade para portaria (Raio-X)")
async def quick_lookup(
    q: str = Query(..., min_length=1, description="Número, bloco ou nome do morador"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[UnitOverviewResponse]:
    """Retorna dados consolidados da unidade (morador, encomendas pendentes e visitantes de hoje) para a guarita."""
    if current_user.tipo_usuario == "MORADOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito à portaria e administração."
        )
    service = UnitService(db)
    return await service.quick_lookup(condominio_id=current_user.condominio_id, query=q)



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
    return await service.list_units(condominio_id=current_user.condominio_id, include_inactive=include_inactive)


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
    return await service.get_unit(unit_id, condominio_id=current_user.condominio_id)


@router.get("/{unit_id}/overview", response_model=UnitOverviewResponse, summary="Raio-X consolidado de uma unidade específica")
async def get_unit_overview(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UnitOverviewResponse:
    """Busca o raio-x consolidado da unidade (morador, encomendas pendentes e visitantes de hoje)."""
    if current_user.tipo_usuario == "MORADOR" and current_user.unidade_id != unit_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: Você só pode consultar os dados da sua própria unidade."
        )
    service = UnitService(db)
    return await service.get_unit_overview(unit_id=unit_id, condominio_id=current_user.condominio_id)



@router.post("", response_model=UnitResponse, summary="Cadastrar nova unidade (Síndico)")
async def create_unit(
    payload: UnitCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Permite ao síndico registrar novos apartamentos/blocos no condomínio."""
    condo_id = _admin.condominio_id
    if not condo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operador administrativo não possui condomínio associado."
        )
    service = UnitService(db)
    return await service.create_unit(payload, condominio_id=condo_id)


@router.post("/batch", response_model=UnitBatchResponse, summary="Gerar andares e apartamentos em lote (Síndico)")
async def create_units_batch(
    payload: UnitBatchCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitBatchResponse:
    """Permite ao síndico criar todos os apartamentos de múltiplos andares com 1 clique."""
    condo_id = _admin.condominio_id
    if not condo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operador administrativo não possui condomínio associado."
        )
    service = UnitService(db)
    return await service.create_units_batch(condominio_id=condo_id, data=payload)


@router.put("/{unit_id}", response_model=UnitResponse, summary="Atualizar apartamento (ativar/desativar) (Síndico)")
async def update_unit(
    unit_id: int,
    payload: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Permite ao síndico alterar dados ou ativar/desativar uma unidade."""
    service = UnitService(db)
    return await service.update_unit(unit_id, payload, condominio_id=_admin.condominio_id)


@router.put("/{unit_id}/assign", response_model=UnitResponse, summary="Vincular morador a um apartamento (Síndico)")
async def assign_resident(
    unit_id: int,
    payload: AssignResidentRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Associa um morador cadastrado ao apartamento selecionado."""
    service = UnitService(db)
    return await service.assign_resident(unit_id, payload.morador_id, condominio_id=_admin.condominio_id)


@router.post("/{unit_id}/invite", response_model=UnitResponse, summary="Convidar morador para auto-cadastro na unidade (Síndico)")
async def invite_resident(
    unit_id: int,
    payload: InviteResidentRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Síndico cadastra morador informando apenas nome e e-mail; o morador recebe link de ativação."""
    condo_id = _admin.condominio_id
    if not condo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operador administrativo não possui condomínio associado."
        )
    service = UnitService(db)
    return await service.invite_resident(unit_id=unit_id, condominio_id=condo_id, data=payload)


@router.post("/{unit_id}/resend-invite", response_model=UnitResponse, summary="Reenviar convite de ativação ao morador (Síndico)")
async def resend_invite(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UnitResponse:
    """Reenvia o e-mail de ativação para o morador pendente."""
    condo_id = _admin.condominio_id
    if not condo_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Operador administrativo não possui condomínio associado."
        )
    service = UnitService(db)
    return await service.resend_invite(unit_id=unit_id, condominio_id=condo_id)

