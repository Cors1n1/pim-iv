from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CondoSettingsPublicResponse(BaseModel):
    condominio_id: Optional[int] = 1
    slug: Optional[str] = None
    nome_condominio: str
    endereco: Optional[str] = None
    telefone_portaria: Optional[str] = None
    email_contato: Optional[str] = None
    cor_primaria: Optional[str] = "#2563eb"
    cor_secundaria: Optional[str] = "#1d4ed8"
    cor_sidebar: Optional[str] = "#09090b"
    cor_fundo: Optional[str] = "AUTO"
    logo_url: Optional[str] = None
    suporte_email: Optional[str] = "suporte@condohub.com.br"
    suporte_telefone: Optional[str] = "(11) 98765-4321"
    suporte_horario: Optional[str] = "Segunda a Sexta, das 08h às 18h"
    titulo_regularizacao: Optional[str] = "O que fazer para regularizar?"
    mensagem_regularizacao: Optional[str] = "Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real."
    titulo_suspensao: Optional[str] = "Acesso ao Condomínio Suspenso"
    subtitulo_suspensao: Optional[str] = "O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central."
    tipo_gestao: Optional[str] = "AUTOGESTAO"
    administradora_nome: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PlatformSettingsResponse(BaseModel):
    id: int = 1
    suporte_email: str
    suporte_telefone: str
    suporte_horario: Optional[str] = "Segunda a Sexta, das 08h às 18h"
    titulo_regularizacao: Optional[str] = "O que fazer para regularizar?"
    mensagem_regularizacao: Optional[str] = "Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real."
    titulo_suspensao: Optional[str] = "Acesso ao Condomínio Suspenso"
    subtitulo_suspensao: Optional[str] = "O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central."
    atualizado_em: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlatformSettingsUpdate(BaseModel):
    suporte_email: Optional[str] = Field(None, min_length=3, max_length=150)
    suporte_telefone: Optional[str] = Field(None, min_length=3, max_length=50)
    suporte_horario: Optional[str] = Field(None, max_length=100)
    titulo_regularizacao: Optional[str] = Field(None, max_length=150)
    mensagem_regularizacao: Optional[str] = Field(None, max_length=5000)
    titulo_suspensao: Optional[str] = Field(None, max_length=150)
    subtitulo_suspensao: Optional[str] = Field(None, max_length=255)


class CondoSettingsResponse(BaseModel):
    id: int
    condominio_id: Optional[int] = 1
    nome_condominio: str
    endereco: Optional[str] = None
    telefone_portaria: Optional[str] = None
    email_contato: Optional[str] = None
    cor_primaria: Optional[str] = "#2563eb"
    cor_secundaria: Optional[str] = "#1d4ed8"
    cor_sidebar: Optional[str] = "#09090b"
    cor_fundo: Optional[str] = "AUTO"
    logo_url: Optional[str] = None
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
    cor_primaria: Optional[str] = Field(None, max_length=20)
    cor_secundaria: Optional[str] = Field(None, max_length=20)
    cor_sidebar: Optional[str] = Field(None, max_length=20)
    cor_fundo: Optional[str] = Field(None, max_length=20)
    logo_url: Optional[str] = Field(None, max_length=255)
    prazo_retomada_horas: Optional[int] = Field(None, ge=1, le=168)
    prazo_standby_horas: Optional[int] = Field(None, ge=1, le=168)
    intervalo_padrao_dias: Optional[int] = Field(None, ge=1, le=365)
    dias_penalidade_queima: Optional[int] = Field(None, ge=1, le=365)
    queima_prioridade_cancelamento: Optional[bool] = None
    enviar_email_ativo: Optional[bool] = None

    @field_validator(
        "nome_condominio",
        "endereco",
        "telefone_portaria",
        "email_contato",
        "cor_primaria",
        "cor_secundaria",
        "cor_sidebar",
        "cor_fundo",
        "logo_url",
        mode="before"
    )
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v
