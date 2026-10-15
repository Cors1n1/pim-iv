from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

UserRole = Literal["ADMIN", "SINDICO", "PORTARIA", "MORADOR"]


class UserBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=150, description="Nome completo do usuário")
    email: EmailStr = Field(..., description="E-mail único de acesso")
    telefone: Optional[str] = Field(None, max_length=20, description="Telefone de contato")
    tipo_usuario: UserRole = Field(..., description="Perfil de acesso no condomínio")


class UserCreate(UserBase):
    senha: str = Field(..., min_length=6, max_length=100, description="Senha de acesso em texto puro")
    unidade_id: Optional[int] = Field(None, description="ID da unidade/apartamento do morador")


class UserResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    telefone: Optional[str]
    tipo_usuario: str
    ativo: bool
    precisa_trocar_senha: bool = False
    unidade_id: Optional[int] = None
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="E-mail de acesso")
    senha: str = Field(..., min_length=1, description="Senha de acesso")


class ChangePasswordRequest(BaseModel):
    senha_atual: str = Field(..., min_length=1, description="Senha temporária ou atual")
    nova_senha: str = Field(..., min_length=6, max_length=100, description="Nova senha definida pelo usuário")
    confirmacao_senha: str = Field(..., min_length=6, max_length=100, description="Confirmação da nova senha")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
