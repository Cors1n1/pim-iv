from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

VisitorType = Literal["VISITANTE", "PRESTADOR_SERVICO", "DELIVERY"]
VisitorStatus = Literal["AGUARDANDO", "NO_LOCAL", "FINALIZADO", "CANCELADO"]


class VisitorCreate(BaseModel):
    unidade_id: Optional[int] = Field(None, description="ID da unidade de destino (opcional para morador logado)")
    nome: str = Field(..., min_length=2, max_length=150, description="Nome completo do visitante")
    documento: Optional[str] = Field(None, max_length=30, description="Documento de identidade (RG ou CPF)")
    tipo: VisitorType = Field("VISITANTE", description="Tipo de visitante")
    data_prevista: date = Field(..., description="Data prevista da visita")
    observacoes: Optional[str] = Field(None, max_length=255, description="Observações ou motivo da visita")


class VisitorEntry(BaseModel):
    documento: Optional[str] = Field(None, max_length=30, description="Documento conferido na entrada")
    observacoes: Optional[str] = Field(None, max_length=255, description="Observação anotada na portaria")


class VisitorResponse(BaseModel):
    id: int
    unidade_id: int
    unidade_desc: str
    autorizado_por_id: Optional[int] = None
    autorizado_por_nome: Optional[str] = None
    nome: str
    documento: Optional[str] = None
    tipo: str
    data_prevista: date
    status: str
    hora_entrada: Optional[datetime] = None
    porteiro_entrada_nome: Optional[str] = None
    hora_saida: Optional[datetime] = None
    porteiro_saida_nome: Optional[str] = None
    observacoes: Optional[str] = None
    is_my_unit: bool = False
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)
