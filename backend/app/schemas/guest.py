from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GuestCreate(BaseModel):
    nome_completo: str = Field(..., min_length=2, max_length=150, description="Nome completo do convidado")
    documento: Optional[str] = Field(None, max_length=50, description="RG ou CPF do convidado para a portaria")
    email: Optional[str] = Field(None, max_length=150, description="E-mail para envio do convite digital")
    enviar_convite: bool = Field(False, description="Disparar convite por e-mail imediatamente")


class GuestBatchCreate(BaseModel):
    convidados: List[GuestCreate]


class GuestResponse(BaseModel):
    id: int
    reserva_id: int
    nome_completo: str
    documento: Optional[str] = None
    email: Optional[str] = None
    convite_enviado: bool
    entrada_registrada: bool
    entrada_em: Optional[datetime] = None
    saida_registrada: bool = False
    saida_em: Optional[datetime] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
