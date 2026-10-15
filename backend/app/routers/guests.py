from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.routers.deps import get_current_user, get_db
from app.schemas.guest import GuestCreate, GuestResponse
from app.services.guest_service import GuestService

router = APIRouter(prefix="/api/guests", tags=["Convidados de Reservas"])


@router.get("/today", summary="Listar convidados de todos os eventos de hoje (visão da portaria)")
async def list_today_guests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[dict]:
    """Retorna os convidados esperados para todas as reservas ativas do dia de hoje."""
    service = GuestService(db)
    return await service.list_today_guests(current_user=current_user)


@router.get("/reservation/{reservation_id}", response_model=List[GuestResponse], summary="Listar convidados de uma reserva")
async def list_guests_by_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[GuestResponse]:
    """Retorna os convidados cadastrados para a reserva informada."""
    service = GuestService(db)
    return await service.list_guests(current_user=current_user, reservation_id=reservation_id)


@router.post("/reservation/{reservation_id}", response_model=GuestResponse, status_code=201, summary="Adicionar convidado à reserva")
async def add_guest_to_reservation(
    reservation_id: int,
    payload: GuestCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> GuestResponse:
    """Adiciona um convidado e opcionalmente despacha o convite digital por e-mail em background."""
    service = GuestService(db)
    return await service.add_guest(
        current_user=current_user,
        reservation_id=reservation_id,
        data=payload,
        background_tasks=background_tasks
    )


@router.delete("/{guest_id}", summary="Remover convidado da lista")
async def delete_guest(
    guest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Remove um convidado da lista da reserva."""
    service = GuestService(db)
    guest = await service.guest_repo.get_by_id(guest_id)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado.")
    return await service.delete_guest(current_user=current_user, reservation_id=guest.reserva_id, guest_id=guest_id)


@router.put("/{guest_id}/checkin", response_model=GuestResponse, summary="Registrar entrada do convidado na portaria")
async def checkin_guest(
    guest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> GuestResponse:
    """Registra a presença e horário de chegada do convidado pela portaria."""
    service = GuestService(db)
    guest = await service.guest_repo.get_by_id(guest_id)
    if not guest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado.")
    return await service.checkin_guest(current_user=current_user, reservation_id=guest.reserva_id, guest_id=guest_id)


@router.put("/{guest_id}/checkout", response_model=GuestResponse, summary="Registrar saída do convidado na portaria")
async def checkout_guest(
    guest_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> GuestResponse:
    """Registra o horário de saída do convidado pela portaria."""
    service = GuestService(db)
    return await service.checkout_guest(current_user=current_user, guest_id=guest_id)


@router.post("/{guest_id}/send-invite", response_model=GuestResponse, summary="Reenviar convite digital por e-mail")
async def resend_guest_invite(
    guest_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> GuestResponse:
    """Reenvia o convite digital corporativo com instruções e dados do condomínio para o e-mail do convidado."""
    service = GuestService(db)
    return await service.resend_invite(current_user=current_user, guest_id=guest_id, background_tasks=background_tasks)
