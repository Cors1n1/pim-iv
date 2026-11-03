from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DeliveryCreate(BaseModel):
    unidade_id: int = Field(..., description="ID da unidade/apartamento destinatário")
    descricao: str = Field(..., min_length=2, max_length=255, description="Descrição da encomenda (ex: Pacote Amazon)")
    codigo_rastreio: Optional[str] = Field(None, max_length=100, description="Código de rastreio ou nota")


class DeliveryDeliver(BaseModel):
    retirado_por: Optional[str] = Field(None, max_length=150, description="Nome de quem retirou a encomenda na portaria")


class UnitInDelivery(BaseModel):
    id: int
    bloco: str
    numero: str

    model_config = ConfigDict(from_attributes=True)


class DeliveryResponse(BaseModel):
    id: int
    unidade_id: int
    unidade: Optional[UnitInDelivery] = None
    descricao: str
    codigo_rastreio: Optional[str]
    status: str
    data_chegada: datetime
    data_retirada: Optional[datetime]
    retirado_por: Optional[str]
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class DeliveryBatchDeliver(BaseModel):
    delivery_ids: Optional[list[int]] = Field(None, description="Lista de IDs de encomendas para dar baixa em lote")
    unidade_id: Optional[int] = Field(None, description="Se fornecido, dá baixa em todas as encomendas pendentes desta unidade")
    retirado_por: Optional[str] = Field(None, max_length=150, description="Nome de quem retirou as encomendas na portaria")


class DeliveryBatchDeliverResponse(BaseModel):
    delivered_count: int
    deliveries: list[DeliveryResponse]

