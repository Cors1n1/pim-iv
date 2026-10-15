from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db
from app.schemas.ticket import TicketCreate, TicketReply, TicketResponse
from app.services.ticket_service import TicketService

router = APIRouter(prefix="/api/tickets", tags=["Livro de Ocorrências & Chamados"])


@router.get("", response_model=List[TicketResponse], summary="Listar ocorrências e chamados")
async def list_tickets(
    status: Optional[str] = Query(None, description="Filtrar por ABERTO, EM_ANALISE, CONCLUIDO ou CANCELADO"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TicketResponse]:
    """Retorna ocorrências: moradores vêem as suas; administração vê todas."""
    service = TicketService(db)
    return await service.list_tickets(current_user=current_user, status_filter=status)


@router.post("", response_model=TicketResponse, summary="Abrir nova ocorrência (Morador/Síndico)")
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TicketResponse:
    """Registra uma ocorrência de barulho, manutenção, vazamento ou segurança."""
    service = TicketService(db)
    return await service.create_ticket(current_user=current_user, data=payload)


@router.put("/{ticket_id}/reply", response_model=TicketResponse, summary="Responder ocorrência (Síndico/Admin)")
async def reply_ticket(
    ticket_id: int,
    payload: TicketReply,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TicketResponse:
    """Registra o parecer oficial da administração do condomínio."""
    service = TicketService(db)
    return await service.reply_ticket(current_user=current_user, ticket_id=ticket_id, data=payload)


@router.put("/{ticket_id}/cancel", response_model=TicketResponse, summary="Cancelar ocorrência")
async def cancel_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TicketResponse:
    """Permite ao autor cancelar uma ocorrência ainda aberta."""
    service = TicketService(db)
    return await service.cancel_ticket(current_user=current_user, ticket_id=ticket_id)
