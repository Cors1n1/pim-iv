from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db
from app.schemas.delivery import DeliveryCreate, DeliveryDeliver, DeliveryResponse
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/api/deliveries", tags=["Portaria & Encomendas"])


@router.get("", response_model=List[DeliveryResponse], summary="Listar encomendas (Morador vê apenas as suas)")
async def list_deliveries(
    status: Optional[str] = Query(None, description="Filtrar por AGUARDANDO_RETIRADA ou ENTREGUE"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[DeliveryResponse]:
    """
    Retorna as encomendas do condomínio.
    - Se for morador: retorna somente as encomendas do seu apartamento (LGPD).
    - Se for portaria/síndico: retorna a lista geral de todas as unidades.
    """
    service = DeliveryService(db)
    return await service.get_deliveries_for_user(current_user=current_user, status_filter=status)


@router.get("/pending-count", summary="Obter contagem de encomendas pendentes de retirada")
async def get_pending_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Retorna o número de encomendas aguardando retirada no escopo do usuário."""
    service = DeliveryService(db)
    count = await service.get_pending_count(current_user)
    return {"pending_count": count}


@router.post("", response_model=DeliveryResponse, summary="Registrar chegada de encomenda (Portaria/Síndico)")
async def create_delivery(
    payload: DeliveryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeliveryResponse:
    """Registra o recebimento de uma nova encomenda na portaria."""
    service = DeliveryService(db)
    return await service.register_delivery(current_user=current_user, data=payload)


@router.put("/{delivery_id}/deliver", response_model=DeliveryResponse, summary="Dar baixa na entrega ao morador")
async def mark_delivered(
    delivery_id: int,
    payload: DeliveryDeliver,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeliveryResponse:
    """Marca a encomenda como entregue quando o morador retira na guarita."""
    service = DeliveryService(db)
    return await service.mark_as_delivered(current_user=current_user, delivery_id=delivery_id, data=payload)
