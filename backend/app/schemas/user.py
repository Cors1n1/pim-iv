from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_strong_password

UserRole = Literal["DIRETORIA", "SUPERADMIN", "ADMIN", "SINDICO", "PORTARIA", "MORADOR"]


class UserBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail único de acesso")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone de contato")
    tipo_usuario: UserRole = Field(..., description="Perfil de acesso no condomínio")


class UserCreate(UserBase):
    senha: str = Field(..., min_length=8, max_length=100, description="Senha de acesso em texto puro")
    unidade_id: Optional[int] = Field(None, description="ID da unidade/apartamento do morador")
    condominio_id: Optional[int] = Field(None, description="ID do condomínio ao qual pertence")

    @field_validator("senha")
    @classmethod
    def validate_user_password(cls, v: str) -> str:
        return validate_strong_password(v)


class UserResponse(BaseModel):
    id: int
    condominio_id: Optional[int] = None
    condominio_nome: Optional[str] = None
    condominio_slug: Optional[str] = None
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    tipo_usuario: str
    ativo: bool
    precisa_trocar_senha: bool = False
    status_cadastro: Optional[str] = "ATIVO"
    token_version: Optional[int] = 1
    cpf: Optional[str] = None
    unidade_id: Optional[int] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail de acesso")
    senha: str = Field(..., min_length=1, description="Senha de acesso")
    condo_slug: Optional[str] = Field(None, description="Slug do condomínio no portal em que o login está sendo realizado")


class ChangePasswordRequest(BaseModel):
    senha_atual: str = Field(..., min_length=1, description="Senha temporária ou atual")
    nova_senha: str = Field(..., min_length=8, max_length=100, description="Nova senha definida pelo usuário")
    confirmacao_senha: str = Field(..., min_length=8, max_length=100, description="Confirmação da nova senha")

    @field_validator("nova_senha")
    @classmethod
    def validate_new_pass(cls, v: str) -> str:
        return validate_strong_password(v)


class ResetUserPasswordRequest(BaseModel):
    nova_senha: str = Field(..., min_length=8, max_length=100, description="Nova senha definida para o usuário")
    precisa_trocar_senha: Optional[bool] = Field(default=False, description="Exigir troca obrigatória de senha no próximo login")

    @field_validator("nova_senha")
    @classmethod
    def validate_reset_pass(cls, v: str) -> str:
        return validate_strong_password(v)


class InviteInfoResponse(BaseModel):
    token: str
    nome: str
    email: str
    tipo_usuario: str
    condominio_id: int
    condominio_nome: str
    condominio_slug: Optional[str] = None
    cor_primaria: Optional[str] = "#2563eb"
    cor_sidebar: Optional[str] = "#09090b"
    bloco: Optional[str] = None
    numero: Optional[str] = None


class CompleteInviteRequest(BaseModel):
    token: str = Field(..., description="Token de convite recebido por e-mail")
    nome_completo: str = Field(..., min_length=3, max_length=150, description="Nome completo oficial do morador")
    telefone: str = Field(..., min_length=8, max_length=20, description="Telefone / WhatsApp para contato")
    cpf: Optional[str] = Field(None, max_length=20, description="CPF do morador")
    senha: str = Field(..., min_length=8, max_length=100, description="Senha definida pelo usuário")
    confirmacao_senha: str = Field(..., min_length=8, max_length=100, description="Confirmação da senha")

    @field_validator("senha")
    @classmethod
    def validate_invite_pass(cls, v: str) -> str:
        return validate_strong_password(v)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GlobalUserResponse(BaseModel):
    id: int
    condominio_id: Optional[int] = None
    condominio_nome: Optional[str] = None
    nome: str
    email: EmailStr
    telefone: Optional[str] = None
    tipo_usuario: str
    ativo: bool
    unidade_id: Optional[int] = None
    unidade_identificador: Optional[str] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class GlobalUserUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=150)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    tipo_usuario: Optional[UserRole] = None
    condominio_id: Optional[int] = None
    unidade_id: Optional[int] = None
    ativo: Optional[bool] = None
    nova_senha: Optional[str] = Field(None, min_length=6, max_length=100)


class BroadcastNoticeRequest(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=150, description="Título do comunicado oficial")
    mensagem: str = Field(..., min_length=5, description="Corpo do comunicado")
    categoria: str = Field("GERAL", description="Categoria do comunicado")
    condominio_id: Optional[int] = Field(None, description="ID do condomínio ou None para broadcast geral em todos")

