from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    telefone: Optional[str] = None
    status_cadastro: Optional[str] = "ATIVO"

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


class UnitBatchCreate(BaseModel):
    bloco: str = Field(..., min_length=1, max_length=20, description="Identificação do bloco (ex: Bloco A)")
    andar_inicial: int = Field(..., ge=0, le=100, description="Andar inicial (ex: 1)")
    andar_final: int = Field(..., ge=0, le=100, description="Andar final (ex: 10)")
    aptos_por_andar: int = Field(..., ge=1, le=50, description="Quantidade de apartamentos por andar (ex: 4)")
    formato_numeracao: str = Field(
        default="CENTENA",
        pattern="^(CENTENA|DEZENA)$",
        description="Formato de numeração: 'CENTENA' (ex: 101, 102...) ou 'DEZENA' (ex: 11, 12...)"
    )

    @model_validator(mode="after")
    def _validate_floor_range(self) -> "UnitBatchCreate":
        if self.andar_final < self.andar_inicial:
            raise ValueError("O andar final deve ser maior ou igual ao andar inicial.")
        return self


class UnitBatchResponse(BaseModel):
    total_criados: int
    total_duplicados: int
    unidades: list[UnitResponse]


class InviteResidentRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, description="Primeiro nome ou nome informal do morador")
    email: str = Field(..., description="E-mail de acesso para onde será enviado o convite")
    tipo_usuario: str = Field(default="MORADOR", description="Perfil do usuário (MORADOR ou PORTARIA)")


class UnitDeliveryBrief(BaseModel):
    id: int
    descricao: str
    codigo_rastreio: Optional[str] = None
    data_chegada: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class UnitVisitorBrief(BaseModel):
    id: int
    nome: str
    documento: Optional[str] = None
    tipo: str
    status: str
    data_prevista: date
    observacoes: Optional[str] = None
    hora_entrada: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnitOverviewResponse(BaseModel):
    id: int
    bloco: str
    numero: str
    andar: Optional[int] = None
    ativo: bool
    morador: Optional[ResidentBrief] = None
    encomendas_pendentes: list[UnitDeliveryBrief] = []
    visitantes_hoje: list[UnitVisitorBrief] = []

    model_config = ConfigDict(from_attributes=True)


