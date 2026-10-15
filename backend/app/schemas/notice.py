from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NoticeCreate(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=150, description="Título do aviso ou comunicado")
    mensagem: str = Field(..., min_length=5, description="Conteúdo descritivo do comunicado")
    categoria: str = Field(default="GERAL", description="Categoria: GERAL, MANUTENCAO, URGENTE, ASSEMBLEIA")
    link_anexo: Optional[str] = Field(None, max_length=500, description="Link para Google Meet, Zoom, YouTube ou documento externo")


class NoticeResponse(BaseModel):
    id: int
    titulo: str
    mensagem: str
    categoria: str
    link_anexo: Optional[str] = None
    autor_id: int
    autor_nome: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime

    model_config = ConfigDict(from_attributes=True)
