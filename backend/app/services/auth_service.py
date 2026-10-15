from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.unit_repository import UnitRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import ChangePasswordRequest, LoginRequest, TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = UserRepository(db)
        self.unit_repository = UnitRepository(db)

    async def authenticate(
        self,
        login_data: LoginRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """
        Autentica credenciais, valida status ativo, grava auditoria
        e gera token JWT padronizado.
        """
        user = await self.repository.get_by_email(login_data.email)

        # Proteção contra timing attack e enumeração de usuários (OWASP)
        is_password_valid = False
        if user:
            is_password_valid = verify_password(login_data.senha, user.senha_hash)

        if not user or not is_password_valid:
            # Registra falha de acesso para auditoria
            await self.repository.log_access(
                user_id=user.id if user else None,
                email=login_data.email,
                ip=client_ip,
                user_agent=user_agent,
                sucesso=False
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.ativo:
            await self.repository.log_access(
                user_id=user.id,
                email=login_data.email,
                ip=client_ip,
                user_agent=user_agent,
                sucesso=False
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo. Contate a administração do condomínio."
            )

        # Registra sucesso de login
        await self.repository.log_access(
            user_id=user.id,
            email=login_data.email,
            ip=client_ip,
            user_agent=user_agent,
            sucesso=True
        )

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tipo_usuario": user.tipo_usuario
        }
        access_token = create_access_token(data=token_data)

        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    async def register_new_user(self, user_data: UserCreate) -> UserResponse:
        """Cadastra um novo morador ou atualiza/vincula morador existente na unidade."""
        existing_user = await self.repository.get_by_email(user_data.email)
        
        # Se o morador já existia no banco, atualiza dados, redefine senha e vincula
        if existing_user:
            if existing_user.tipo_usuario == "MORADOR":
                existing_user.nome = user_data.nome
                if user_data.telefone:
                    existing_user.telefone = user_data.telefone
                existing_user.senha_hash = get_password_hash(user_data.senha)
                existing_user.ativo = True
                existing_user.precisa_trocar_senha = True
                await self.repository.update(existing_user)

                if user_data.unidade_id:
                    await self.unit_repository.assign_resident(user_data.unidade_id, existing_user.id)
                    await self.db.refresh(existing_user)

                return UserResponse.model_validate(existing_user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este e-mail pertence a um usuário administrativo do condomínio."
                )

        hashed_password = get_password_hash(user_data.senha)
        new_user = User(
            nome=user_data.nome,
            email=user_data.email,
            senha_hash=hashed_password,
            telefone=user_data.telefone,
            tipo_usuario=user_data.tipo_usuario,
            unidade_id=user_data.unidade_id,
            ativo=True,
            precisa_trocar_senha=(user_data.tipo_usuario == "MORADOR")
        )

        created = await self.repository.create(new_user)

        # Se foi informado unidade_id e for perfil MORADOR, vincula como responsável da unidade
        if user_data.unidade_id and user_data.tipo_usuario == "MORADOR":
            await self.unit_repository.assign_resident(user_data.unidade_id, created.id)
            await self.db.refresh(created)

        return UserResponse.model_validate(created)

    async def change_password(
        self,
        user_id: int,
        change_data: ChangePasswordRequest
    ) -> UserResponse:
        """Altera a senha do usuário e remove a flag de primeiro acesso."""
        if change_data.nova_senha != change_data.confirmacao_senha:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nova senha e a confirmação de senha não coincidem."
            )

        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )

        if not verify_password(change_data.senha_atual, user.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha atual informada está incorreta."
            )

        if verify_password(change_data.nova_senha, user.senha_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nova senha deve ser diferente da senha anterior."
            )

        new_hash = get_password_hash(change_data.nova_senha)
        updated_user = await self.repository.update_password(
            user_id=user.id,
            new_password_hash=new_hash,
            precisa_trocar_senha=False
        )

        return UserResponse.model_validate(updated_user)

    async def get_current_user_profile(self, user_id: int) -> UserResponse:
        """Obtém os dados do perfil do usuário autenticado."""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado."
            )
        return UserResponse.model_validate(user)
