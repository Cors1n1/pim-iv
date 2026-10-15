from datetime import date
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db
from app.schemas.reservation import (
    CommonAreaCreate,
    CommonAreaResponse,
    CommonAreaUpdate,
    KeyHandoverRequest,
    ReservationCreate,
    ReservationPriorityCheckResponse,
    ReservationResponse
)
from app.services.reservation_service import ReservationService

router = APIRouter(prefix="/api/reservations", tags=["Reservas de Áreas Comuns"])


@router.get("/priority-check", response_model=ReservationPriorityCheckResponse, summary="Verificar prioridade de agendamento")
async def check_reservation_priority(
    area_id: int,
    data_reserva: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationPriorityCheckResponse:
    """Verifica se a unidade do condômino possui Alta Prioridade ou Baixa Prioridade (Standby) para a data informada."""
    service = ReservationService(db)
    return await service.check_priority(current_user=current_user, area_id=area_id, data_reserva=data_reserva)


@router.get("/areas", response_model=List[CommonAreaResponse], summary="Listar áreas comuns disponíveis")
async def list_common_areas(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> List[CommonAreaResponse]:
    """Retorna a lista de salão de festas, churrasqueira, etc. com regras de horário."""
    service = ReservationService(db)
    return await service.list_common_areas(include_inactive=include_inactive)


@router.post("/areas", response_model=CommonAreaResponse, summary="Criar nova área comum (exclusivo síndico)")
async def create_common_area(
    payload: CommonAreaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CommonAreaResponse:
    """Permite ao síndico cadastrar um novo espaço comum com seus limites de horário."""
    service = ReservationService(db)
    return await service.create_common_area(current_user=current_user, data=payload)


@router.put("/areas/{area_id}", response_model=CommonAreaResponse, summary="Atualizar regras operacionais de área comum (exclusivo síndico)")
async def update_common_area(
    area_id: int,
    payload: CommonAreaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CommonAreaResponse:
    """Permite ao síndico alterar horário de abertura, fechamento e tempo máximo de uso sem mexer no código."""
    service = ReservationService(db)
    return await service.update_common_area(current_user=current_user, area_id=area_id, data=payload)


@router.get("", response_model=List[ReservationResponse], summary="Listar reservas de áreas comuns (com proteção LGPD)")
async def list_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ReservationResponse]:
    """
    Retorna o cronograma de reservas:
    - Moradores visualizam os agendamentos alheios de forma anônima (LGPD).
    - Síndicos e portaria visualizam a identificação completa para controle de acesso e entrega de chaves.
    """
    service = ReservationService(db)
    return await service.list_reservations_for_user(current_user)


@router.post("", response_model=ReservationResponse, summary="Solicitar reserva de área comum (exclusivo moradores e síndicos)")
async def create_reservation(
    payload: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationResponse:
    """Agenda uma data para uso da área comum, aplicando as regras de prioridade e validação de disponibilidade."""
    service = ReservationService(db)
    return await service.create_reservation(current_user=current_user, data=payload)


@router.put("/{reservation_id}/cancel", response_model=ReservationResponse, summary="Cancelar reserva de área comum")
async def cancel_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationResponse:
    """Cancela uma reserva previamente confirmada."""
    service = ReservationService(db)
    return await service.cancel_reservation(current_user=current_user, reservation_id=reservation_id)


@router.put("/{reservation_id}/handover-key", response_model=ReservationResponse, summary="Registrar entrega da chave (portaria/administração)")
async def handover_key(
    reservation_id: int,
    payload: KeyHandoverRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationResponse:
    """Anota na portaria para quem a chave do espaço foi entregue e a data/hora."""
    service = ReservationService(db)
    return await service.handover_key(current_user=current_user, reservation_id=reservation_id, entregue_para=payload.entregue_para)


@router.put("/{reservation_id}/return-key", response_model=ReservationResponse, summary="Registrar devolução da chave (portaria/administração)")
async def return_key(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationResponse:
    """Anota na portaria que a chave do espaço foi devolvida."""
    service = ReservationService(db)
    return await service.return_key(current_user=current_user, reservation_id=reservation_id)


@router.get("/active-offers", response_model=List[ReservationResponse], summary="Listar ofertas ativas de retomada de vaga para o condômino")
async def list_active_offers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ReservationResponse]:
    """Retorna ofertas com direito de preferência pendentes para o condômino."""
    service = ReservationService(db)
    return await service.list_active_offers(current_user)


@router.post("/{reservation_id}/accept-offer", response_model=ReservationResponse, summary="Aceitar oferta de retomada de vaga")
async def accept_offer(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationResponse:
    """Aceita a vaga oferecida com confirmação definitiva imediata."""
    service = ReservationService(db)
    return await service.accept_offer(current_user, reservation_id)


@router.post("/{reservation_id}/decline-offer", response_model=ReservationResponse, summary="Dispensar oferta de retomada de vaga")
async def decline_offer(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReservationResponse:
    """Dispensa a vaga oferecida e a libera para outros condôminos."""
    service = ReservationService(db)
    return await service.decline_offer(current_user, reservation_id)

