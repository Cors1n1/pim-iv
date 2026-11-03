from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_strong_password

CondoPlan = Literal["PADRAO", "BASICO", "PRO", "ENTERPRISE"]
CondoStatus = Literal["ATIVO", "BLOQUEADO", "CANCELADO"]


class CondominioBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, description="Nome oficial do condomínio")
    slug: Optional[str] = Field(None, max_length=100, description="Slug amigável para URL exclusiva (ex: jardins-europa)")
    cnpj: Optional[str] = Field(None, max_length=20, description="CNPJ do condomínio")
    endereco: Optional[str] = Field(None, max_length=255, description="Endereço completo")
    telefone: Optional[str] = Field(None, max_length=50, description="Telefone de contato ou guarita")
    email_contato: Optional[EmailStr] = Field(None, description="E-mail oficial para avisos e notificações")
    plano: Optional[str] = Field("PADRAO", description="Categoria de registro")
    limite_unidades: int = Field(100, ge=1, le=5000, description="Limite máximo de unidades permitidas")
    cor_primaria: str = Field("#2563eb", max_length=20, description="Cor primária para theming CSS")
    cor_secundaria: str = Field("#1d4ed8", max_length=20, description="Cor secundária para theming CSS")
    cor_sidebar: str = Field("#09090b", max_length=20, description="Cor de fundo da barra lateral e topbar")
    logo_url: Optional[str] = Field(None, max_length=255, description="URL ou path do logotipo")


class CondominioCreate(BaseModel):
    nome: Optional[str] = Field(None, max_length=150, description="Nome do condomínio (opcional, síndico define no onboarding)")
    slug: Optional[str] = Field(None, max_length=100, description="Slug amigável para URL exclusiva")
    sindico_nome: str = Field(..., min_length=2, max_length=150, description="Nome ou apelido inicial do síndico")
    sindico_email: EmailStr = Field(..., description="E-mail de acesso do síndico")
    sindico_telefone: Optional[str] = Field(None, max_length=50, description="Telefone ou WhatsApp do síndico")
    sindico_senha: Optional[str] = Field(None, min_length=6, max_length=100, description="Senha inicial opcional (se omitida, gerada automaticamente)")
    
    # Governança: Autogestão (Apenas Síndico) vs Gestão Compartilhada (Síndico + Administradora)
    tipo_gestao: Literal["AUTOGESTAO", "COMPARTILHADA"] = Field("AUTOGESTAO", description="Modelo de gestão: AUTOGESTAO ou COMPARTILHADA")
    administradora_nome: Optional[str] = Field(None, max_length=150, description="Nome da administradora ou gestor parceiro")
    administradora_email: Optional[EmailStr] = Field(None, description="E-mail da administradora para convite de ativação")
    administradora_telefone: Optional[str] = Field(None, max_length=50, description="WhatsApp ou telefone da administradora")

    # Governança de Gestores: Subsíndico(a)
    tem_subsindico: bool = Field(False, description="Indica se o condomínio possui Subsíndico na governança")
    subsindico_nome: Optional[str] = Field(None, max_length=150, description="Nome do Subsíndico(a)")
    subsindico_email: Optional[EmailStr] = Field(None, description="E-mail institucional do Subsíndico(a)")
    subsindico_telefone: Optional[str] = Field(None, max_length=50, description="WhatsApp ou telefone do Subsíndico(a)")

    plano: Optional[str] = Field("PADRAO", description="Categoria de registro")
    limite_unidades: int = Field(100, ge=1, le=5000, description="Limite máximo de unidades permitidas")
    cor_primaria: str = Field("#2563eb", max_length=20, description="Cor primária para theming CSS")
    cor_secundaria: str = Field("#1d4ed8", max_length=20, description="Cor secundária para theming CSS")
    cor_sidebar: Optional[str] = Field("#09090b", max_length=20, description="Cor de fundo da barra lateral e topbar")

    @field_validator(
        "nome",
        "slug",
        "administradora_nome",
        "administradora_email",
        "administradora_telefone",
        "subsindico_nome",
        "subsindico_email",
        "subsindico_telefone",
        "sindico_telefone",
        "sindico_senha",
        mode="before"
    )
    @classmethod
    def sanitize_create_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class CondominioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    slug: Optional[str] = Field(None, max_length=100, description="Slug amigável para URL exclusiva (ex: bela-vista)")
    cnpj: Optional[str] = Field(None, max_length=20)
    endereco: Optional[str] = Field(None, max_length=255)
    telefone: Optional[str] = Field(None, max_length=50)
    email_contato: Optional[EmailStr] = None
    limite_unidades: Optional[int] = Field(None, ge=1, le=5000)
    status: Optional[CondoStatus] = None
    cor_primaria: Optional[str] = Field(None, max_length=20)
    cor_secundaria: Optional[str] = Field(None, max_length=20)
    cor_sidebar: Optional[str] = Field(None, max_length=20)
    logo_url: Optional[str] = Field(None, max_length=255)
    tipo_gestao: Optional[Literal["AUTOGESTAO", "COMPARTILHADA"]] = None
    administradora_nome: Optional[str] = Field(None, max_length=150)
    administradora_email: Optional[EmailStr] = None
    administradora_telefone: Optional[str] = Field(None, max_length=50)
    # Gestão integrada do Síndico
    sindico_nome: Optional[str] = Field(None, min_length=2, max_length=150)
    sindico_email: Optional[EmailStr] = None
    sindico_telefone: Optional[str] = None
    sindico_senha: Optional[str] = Field(None, min_length=6, max_length=100)

    # Gestão integrada de Subsíndico
    tem_subsindico: Optional[bool] = None
    subsindico_nome: Optional[str] = Field(None, min_length=2, max_length=150)
    subsindico_email: Optional[EmailStr] = None
    subsindico_telefone: Optional[str] = None
    subsindico_senha: Optional[str] = Field(None, min_length=6, max_length=100)
    remover_subsindico: Optional[bool] = None

    @field_validator(
        "nome",
        "slug",
        "cnpj",
        "endereco",
        "telefone",
        "email_contato",
        "cor_primaria",
        "cor_secundaria",
        "cor_sidebar",
        "logo_url",
        "administradora_nome",
        "administradora_email",
        "administradora_telefone",
        "sindico_nome",
        "sindico_email",
        "sindico_telefone",
        "sindico_senha",
        "subsindico_nome",
        "subsindico_email",
        "subsindico_telefone",
        "subsindico_senha",
        mode="before"
    )
    @classmethod
    def sanitize_update_strings(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v if v else None
        return v


class CondominioStatusUpdate(BaseModel):
    status: CondoStatus = Field(..., description="Novo status do condomínio (ATIVO, BLOQUEADO, CANCELADO)")
    motivo: Optional[str] = Field(None, max_length=255, description="Motivo do bloqueio ou alteração")


class CondominioThemeResponse(BaseModel):
    id: int
    nome: str
    cor_primaria: str
    cor_secundaria: str
    cor_sidebar: str = "#09090b"
    logo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ResetSindicoPasswordRequest(BaseModel):
    nova_senha: str = Field(..., min_length=6, max_length=100, description="Nova senha para o síndico")


class CondominioResponse(CondominioBase):
    id: int
    status: str
    motivo_bloqueio: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime
    tipo_gestao: Optional[str] = "AUTOGESTAO"
    administradora_nome: Optional[str] = None
    administradora_email: Optional[str] = None
    administradora_id: Optional[int] = None
    administradora_ativo: Optional[bool] = None
    administradora_activation_token: Optional[str] = None
    administradora_activation_url: Optional[str] = None
    total_unidades: Optional[int] = 0
    total_moradores: Optional[int] = 0
    total_porteiros: Optional[int] = 0
    total_encomendas_pendentes: Optional[int] = 0
    total_ocorrencias_abertas: Optional[int] = 0
    total_reservas: Optional[int] = 0
    total_areas_comuns: Optional[int] = 0
    sindico_id: Optional[int] = None
    sindico_nome: Optional[str] = None
    sindico_email: Optional[str] = None
    sindico_telefone: Optional[str] = None
    sindico_ativo: Optional[bool] = True
    tem_subsindico: Optional[bool] = False
    subsindico_id: Optional[int] = None
    subsindico_nome: Optional[str] = None
    subsindico_email: Optional[str] = None
    subsindico_telefone: Optional[str] = None
    subsindico_ativo: Optional[bool] = None
    subsindico_activation_token: Optional[str] = None
    subsindico_activation_url: Optional[str] = None
    activation_token: Optional[str] = None
    activation_url: Optional[str] = None
    senha_provisoria: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SindicoActivationInfoResponse(BaseModel):
    condominio_id: int
    condominio_nome: str
    condominio_slug: str
    condominio_logo: Optional[str] = None
    cor_primaria: str = "#2563eb"
    cor_secundaria: str = "#1d4ed8"
    cor_sidebar: str = "#09090b"
    sindico_nome: str
    sindico_email: str
    tipo_usuario: Optional[str] = "SINDICO"
    papel_descricao: Optional[str] = "Síndico"


class SindicoCompleteActivationRequest(BaseModel):
    token: str = Field(..., description="Token JWT de ativação")
    nova_senha: str = Field(..., min_length=8, max_length=100, description="Nova senha definida pessoalmente pelo síndico")

    @field_validator("nova_senha")
    @classmethod
    def validate_sindico_password(cls, v: str) -> str:
        return validate_strong_password(v)
    nome_completo: str = Field(..., min_length=2, max_length=150, description="Nome completo oficial do síndico")
    telefone: Optional[str] = Field(None, max_length=50, description="WhatsApp ou telefone celular de contato")
    cpf: Optional[str] = Field(None, max_length=20, description="CPF do síndico para conformidade e assinatura")
    # Dados cadastrais definitivos do condomínio (opcionais na ativação)
    nome_condominio: Optional[str] = Field(None, max_length=150, description="Nome oficial definitivo do condomínio")
    slug: Optional[str] = Field(None, max_length=100, description="Slug amigável para URL exclusiva")
    cnpj: Optional[str] = Field(None, max_length=20, description="CNPJ do condomínio")
    endereco: Optional[str] = Field(None, max_length=255, description="Endereço oficial do condomínio")
    telefone_portaria: Optional[str] = Field(None, max_length=50, description="Telefone fixo da portaria ou guarita")


class ResendInviteResponse(BaseModel):
    success: bool
    condominio_id: int
    sindico_email: str
    activation_token: str
    activation_url: str
    senha_provisoria: Optional[str] = None
    message: str

