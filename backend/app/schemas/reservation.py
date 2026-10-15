from datetime import date, datetime, time
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CommonAreaResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    capacidade_pessoas: int
    taxa_limpeza: float
    hora_inicio: time
    hora_fim: time
    duracao_maxima_horas: int
    intervalo_dias_prioridade: int = 30
    max_reservas_ativas: int = 2
    prazo_standby_horas: int = 48
    ativo: bool

    model_config = ConfigDict(from_attributes=True)


class CommonAreaUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=100)
    descricao: Optional[str] = None
    capacidade_pessoas: Optional[int] = Field(None, gt=0)
    taxa_limpeza: Optional[float] = Field(None, ge=0)
    hora_inicio: Optional[time] = None
    hora_fim: Optional[time] = None
    duracao_maxima_horas: Optional[int] = Field(None, gt=0, le=24)
    intervalo_dias_prioridade: Optional[int] = Field(None, ge=1, le=365)
    max_reservas_ativas: Optional[int] = Field(None, ge=1, le=10)
    prazo_standby_horas: Optional[int] = Field(None, ge=1, le=168)
    ativo: Optional[bool] = None


class CommonAreaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: Optional[str] = None
    capacidade_pessoas: int = Field(..., gt=0)
    taxa_limpeza: float = Field(0.0, ge=0)
    hora_inicio: time = Field(default=time(8, 0))
    hora_fim: time = Field(default=time(22, 0))
    duracao_maxima_horas: int = Field(default=4, gt=0, le=24)
    intervalo_dias_prioridade: int = Field(default=30, ge=1, le=365)
    max_reservas_ativas: int = Field(default=2, ge=1, le=10)
    prazo_standby_horas: int = Field(default=48, ge=1, le=168)


class ReservationCreate(BaseModel):
    area_comum_id: int = Field(..., description="ID da área comum a reservar")
    data_reserva: date = Field(..., description="Data da reserva (AAAA-MM-DD)")
    hora_inicio: time = Field(..., description="Horário de início (HH:MM)")
    hora_fim: time = Field(..., description="Horário de término (HH:MM)")
    observacoes: Optional[str] = Field(None, max_length=255, description="Observação ou finalidade")


class ReservationPriorityCheck(BaseModel):
    area_comum_id: int
    data_reserva: date


class ReservationPriorityCheckResponse(BaseModel):
    tem_prioridade_alta: bool
    status_proposto: str  # CONFIRMADA ou BAIXA_PRIORIDADE
    dias_desde_ultima: Optional[int] = None
    intervalo_requerido: int
    reservas_ativas: int
    max_ativas: int
    mensagem: str


class KeyHandoverRequest(BaseModel):
    entregue_para: str = Field(..., min_length=2, max_length=150, description="Nome de quem retirou a chave na portaria")


class ReservationResponse(BaseModel):
    id: int
    area_comum_id: int
    area_nome: str
    data_reserva: date
    hora_inicio: time = time(8, 0)
    hora_fim: time = time(12, 0)
    status: str
    prioridade: str = "ALTA"
    prioridade_queimada: bool = False
    oferta_retomada_ate: Optional[datetime] = None
    total_convidados: int = 0
    morador_nome: str
    unidade_desc: str
    observacoes: Optional[str] = None
    is_mine: bool
    chave_entregue: bool = False
    chave_entregue_para: Optional[str] = None
    chave_entregue_em: Optional[datetime] = None
    chave_devolvida: bool = False
    chave_devolvida_em: Optional[datetime] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
