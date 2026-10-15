from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

TicketCategory = Literal["BARULHO", "MANUTENCAO", "VAZAMENTO", "SEGURANCA", "OUTROS"]
TicketStatus = Literal["ABERTO", "EM_ANALISE", "CONCLUIDO", "CANCELADO"]


class TicketCreate(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=150, description="Título resumido da ocorrência")
    descricao: str = Field(..., min_length=5, description="Descrição detalhada do fato ocorrido")
    categoria: TicketCategory = Field("GERAL", description="Categoria do chamado")
    unidade_id: Optional[int] = Field(None, description="Unidade do morador (opcional, herdado do usuário logado)")


class TicketReply(BaseModel):
    resposta_sindico: str = Field(..., min_length=2, description="Parecer da administração")
    status: TicketStatus = Field("CONCLUIDO", description="Novo status do chamado")


class TicketStatusUpdate(BaseModel):
    status: TicketStatus = Field(..., description="Novo status do chamado")


class TicketResponse(BaseModel):
    id: int
    unidade_id: Optional[int] = None
    unidade_desc: str
    usuario_id: int
    morador_nome: str
    titulo: str
    descricao: str
    categoria: str
    status: str
    resposta_sindico: Optional[str] = None
    respondido_por_nome: Optional[str] = None
    respondido_em: Optional[datetime] = None
    is_mine: bool = False
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)
