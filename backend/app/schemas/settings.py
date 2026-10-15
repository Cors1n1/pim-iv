from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CondoSettingsPublicResponse(BaseModel):
    nome_condominio: str
    endereco: Optional[str] = None
    telefone_portaria: Optional[str] = None
    email_contato: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CondoSettingsResponse(BaseModel):
    id: int
    nome_condominio: str
    endereco: Optional[str] = None
    telefone_portaria: Optional[str] = None
    email_contato: Optional[str] = None
    prazo_retomada_horas: int
    prazo_standby_horas: int
    intervalo_padrao_dias: int
    dias_penalidade_queima: int
    queima_prioridade_cancelamento: bool
    enviar_email_ativo: bool
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CondoSettingsUpdate(BaseModel):
    nome_condominio: Optional[str] = Field(None, min_length=2, max_length=150)
    endereco: Optional[str] = Field(None, max_length=255)
    telefone_portaria: Optional[str] = Field(None, max_length=50)
    email_contato: Optional[str] = Field(None, max_length=100)
    prazo_retomada_horas: Optional[int] = Field(None, ge=1, le=168)
    prazo_standby_horas: Optional[int] = Field(None, ge=1, le=168)
    intervalo_padrao_dias: Optional[int] = Field(None, ge=1, le=365)
    dias_penalidade_queima: Optional[int] = Field(None, ge=1, le=365)
    queima_prioridade_cancelamento: Optional[bool] = None
    enviar_email_ativo: Optional[bool] = None
