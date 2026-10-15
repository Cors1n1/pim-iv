from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UnitBase(BaseModel):
    bloco: str = Field(..., min_length=1, max_length=20, description="Identificação do bloco (ex: Bloco A)")
    numero: str = Field(..., min_length=1, max_length=20, description="Número do apartamento (ex: 101)")
    andar: Optional[int] = Field(None, description="Andar do apartamento")


class UnitCreate(UnitBase):
    morador_responsavel_id: Optional[int] = None


class ResidentBrief(BaseModel):
    id: int
    nome: str
    email: str
    telefone: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class UnitResponse(BaseModel):
    id: int
    bloco: str
    numero: str
    andar: Optional[int]
    morador_responsavel_id: Optional[int]
    morador_responsavel: Optional[ResidentBrief] = None
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class UnitUpdate(BaseModel):
    bloco: Optional[str] = Field(None, min_length=1, max_length=20)
    numero: Optional[str] = Field(None, min_length=1, max_length=20)
    andar: Optional[int] = None
    ativo: Optional[bool] = None


class AssignResidentRequest(BaseModel):
    morador_id: Optional[int] = Field(None, description="ID do usuário a ser vinculado (ou null para desvincular)")
