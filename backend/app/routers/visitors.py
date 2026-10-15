from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db
from app.schemas.visitor import VisitorCreate, VisitorEntry, VisitorResponse
from app.services.visitor_service import VisitorService

router = APIRouter(prefix="/api/visitors", tags=["Controle de Portaria & Visitantes"])


@router.get("", response_model=List[VisitorResponse], summary="Listar visitantes e prestadores")
async def list_visitors(
    status: Optional[str] = Query(None, description="Filtrar por AGUARDANDO, NO_LOCAL, FINALIZADO ou CANCELADO"),
    data_prevista: Optional[date] = Query(None, description="Filtrar por data específica"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[VisitorResponse]:
    """Retorna a lista de acessos: portaria/síndico vê todos; morador vê os da sua unidade."""
    service = VisitorService(db)
    return await service.list_visitors(current_user=current_user, status_filter=status, date_filter=data_prevista)


@router.post("", response_model=VisitorResponse, summary="Pré-autorizar ou registrar visitante")
async def create_visitor(
    payload: VisitorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VisitorResponse:
    """Morador pré-autoriza entrada ou portaria registra visitante na guarita."""
    service = VisitorService(db)
    return await service.create_visitor(current_user=current_user, data=payload)


@router.put("/{visitor_id}/entry", response_model=VisitorResponse, summary="Registrar entrada na portaria")
async def register_entry(
    visitor_id: int,
    payload: Optional[VisitorEntry] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VisitorResponse:
    """Anota que o visitante ingressou no condomínio."""
    service = VisitorService(db)
    return await service.register_entry(current_user=current_user, visitor_id=visitor_id, data=payload)


@router.put("/{visitor_id}/exit", response_model=VisitorResponse, summary="Registrar saída na portaria")
async def register_exit(
    visitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VisitorResponse:
    """Anota que o visitante deixou as dependências do condomínio."""
    service = VisitorService(db)
    return await service.register_exit(current_user=current_user, visitor_id=visitor_id)


@router.put("/{visitor_id}/cancel", response_model=VisitorResponse, summary="Cancelar autorização de visita")
async def cancel_visitor(
    visitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VisitorResponse:
    """Cancela uma autorização antes de ela ser utilizada."""
    service = VisitorService(db)
    return await service.cancel_visitor(current_user=current_user, visitor_id=visitor_id)
