from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limiter import auth_rate_limiter
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.condominio_repository import CondominioRepository
from app.repositories.unit_repository import UnitRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    ChangePasswordRequest,
    CompleteInviteRequest,
    InviteInfoResponse,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse
)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repository = UserRepository(db)
        self.unit_repository = UnitRepository(db)

    async def authenticate(
        self,
        login_data: LoginRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        condo_slug_header: Optional[str] = None
    ) -> TokenResponse:
        """
        Autentica credenciais, valida status ativo, isolamento multi-inquilino (tenant isolation),
        grava auditoria e gera token JWT padronizado.
        """
        client_key = f"ip:{client_ip or 'unknown'}"
        account_key = f"account:{login_data.email.strip().lower()}"
        auth_rate_limiter.check_limit(client_key)
        auth_rate_limiter.check_limit(account_key)

        user = await self.repository.get_by_email(login_data.email)
        if not user and login_data.email.lower() == "admin@condominio.com":
            user = await self.repository.get_by_email("sindico@condominio.com")

        # Verificação de credenciais
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
            # Registra falha no rate limiter
            auth_rate_limiter.record_failure(client_key)
            auth_rate_limiter.record_failure(account_key)
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

        from app.repositories.condominio_repository import CondominioRepository
        condo_repo = CondominioRepository(self.db)

        # -------------------------------------------------------------------------
        # Validação do condomínio de acesso
        # O usuário do condomínio A só pode logar no portal do condomínio A.
        # Usuários com perfil administrativo global podem autenticar nos condomínios da rede.
        # -------------------------------------------------------------------------
        is_global_admin = user.tipo_usuario in ("DIRETORIA", "SUPERADMIN", "ADMIN")
        target_slug = (login_data.condo_slug or condo_slug_header or "").strip().lower()

        active_condo_id = user.condominio_id
        active_condo_nome = None
        active_condo_slug = None

        if target_slug:
            target_condo = await condo_repo.get_by_slug(target_slug)
            if is_global_admin:
                if target_condo:
                    active_condo_id = target_condo.id
                    active_condo_nome = target_condo.nome
                    active_condo_slug = target_condo.slug
            else:
                if not target_condo or user.condominio_id != target_condo.id:
                    # Registra tentativa sem correspondência de condomínio
                    await self.repository.log_access(
                        user_id=user.id,
                        email=login_data.email,
                        ip=client_ip,
                        user_agent=user_agent,
                        sucesso=False
                    )
                    auth_rate_limiter.record_failure(client_key)
                    auth_rate_limiter.record_failure(account_key)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="E-mail ou senha incorretos.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )

        # Se for usuário de condomínio comum, valida se a assinatura do condomínio está ativa
        if active_condo_id and not is_global_admin:
            condo = await condo_repo.get_by_id(active_condo_id)
            if not condo or condo.status != "ATIVO":
                await self.repository.log_access(
                    user_id=user.id,
                    email=login_data.email,
                    ip=client_ip,
                    user_agent=user_agent,
                    sucesso=False
                )
                is_sindico = user.tipo_usuario in ("SINDICO", "ADMIN", "SUBSINDICO")
                motivo = condo.motivo_bloqueio if condo else None
                motivo_msg = f" Motivo: {motivo}." if (motivo and is_sindico) else ""
                status_desc = "cancelado" if (condo and condo.status == "CANCELADO") else "suspenso"
                detail_msg = (
                    f"Acesso {status_desc}. O condomínio está temporariamente pausado.{motivo_msg} Contate o suporte comercial ou administração."
                    if is_sindico
                    else f"Acesso {status_desc}. O portal do condomínio está temporariamente indisponível. Por favor, contate a administração ou o síndico."
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=detail_msg,
                    headers={
                        "X-Condo-Status": condo.status if condo else "INEXISTENTE",
                        "X-User-Role": user.tipo_usuario
                    }
                )

        # Registra sucesso de login e limpa contador de força bruta
        await self.repository.log_access(
            user_id=user.id,
            email=login_data.email,
            ip=client_ip,
            user_agent=user_agent,
            sucesso=True
        )
        auth_rate_limiter.record_success(client_key)
        auth_rate_limiter.record_success(account_key)

        # Determina o papel efetivo no token (impersonação contextual quando admin acessa condomínio)
        is_impersonating = is_global_admin and bool(target_slug or (active_condo_id and user.tipo_usuario in ("DIRETORIA", "SUPERADMIN")))
        effective_role = "SINDICO" if is_impersonating else user.tipo_usuario

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tipo_usuario": effective_role,
            "condominio_id": active_condo_id,
            "token_version": getattr(user, "token_version", 1) or 1,
            "is_impersonation": is_impersonating
        }
        access_token = create_access_token(data=token_data)

        user_response = UserResponse.model_validate(user)
        if active_condo_id:
            if not active_condo_nome or not active_condo_slug:
                u_condo = await condo_repo.get_by_id(active_condo_id)
                if u_condo:
                    active_condo_nome = u_condo.nome
                    active_condo_slug = u_condo.slug
            user_response.condominio_id = active_condo_id
            user_response.condominio_nome = active_condo_nome
            user_response.condominio_slug = active_condo_slug
        if is_impersonating:
            user_response.tipo_usuario = "SINDICO"

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    async def authenticate_console_admin(
        self,
        login_data: LoginRequest,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TokenResponse:
        """Autenticação restrita e corporativa para a Diretoria da plataforma CondoHub."""
        email_clean = login_data.email.strip().lower()
        user = await self.repository.get_by_email(email_clean)
        
        # Suporte a credencial legada ou alias de diretoria
        if not user and email_clean in ("diretoria@condohub.com.br", "superadmin@condohub.com.br"):
            user = await self.repository.get_by_email("diretoria@condohub.com.br")
            if not user:
                user = await self.repository.get_by_email("superadmin@condohub.com.br")

        client_key = f"ip:{client_ip or 'unknown'}"
        account_key = f"account:{email_clean}"
        auth_rate_limiter.check_limit(client_key)
        auth_rate_limiter.check_limit(account_key)

        is_valid = False
        if user and user.tipo_usuario in ("DIRETORIA", "SUPERADMIN"):
            is_valid = verify_password(login_data.senha, user.senha_hash)

        if not user or not is_valid or user.tipo_usuario not in ("DIRETORIA", "SUPERADMIN"):
            await self.repository.log_access(
                user_id=user.id if user else None,
                email=login_data.email,
                ip=client_ip,
                user_agent=user_agent,
                sucesso=False
            )
            auth_rate_limiter.record_failure(client_key)
            auth_rate_limiter.record_failure(account_key)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas para o Console da Diretoria.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.ativo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso corporativo inativo ou suspenso."
            )

        await self.repository.log_access(
            user_id=user.id,
            email=login_data.email,
            ip=client_ip,
            user_agent=user_agent,
            sucesso=True
        )
        auth_rate_limiter.record_success(client_key)
        auth_rate_limiter.record_success(account_key)

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "tipo_usuario": user.tipo_usuario,
            "condominio_id": None,
            "token_version": getattr(user, "token_version", 1) or 1
        }
        access_token = create_access_token(data=token_data)
        user_response = UserResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user_response
        )

    # Alias para compatibilidade
    authenticate_superadmin = authenticate_console_admin

    async def register_new_user(self, user_data: UserCreate, default_condominio_id: Optional[int] = None) -> UserResponse:
        """Cadastra um novo morador ou atualiza/vincula morador existente na unidade."""
        existing_user = await self.repository.get_by_email(user_data.email)
        target_condo_id = user_data.condominio_id or default_condominio_id or 1
        
        # Se o morador já existia no banco, atualiza dados, redefine senha e vincula
        if existing_user:
            if existing_user.tipo_usuario == "MORADOR":
                existing_user.nome = user_data.nome
                if user_data.telefone:
                    existing_user.telefone = user_data.telefone
                existing_user.senha_hash = get_password_hash(user_data.senha)
                existing_user.ativo = True
                existing_user.precisa_trocar_senha = False
                existing_user.condominio_id = target_condo_id
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
            condominio_id=target_condo_id,
            ativo=True,
            precisa_trocar_senha=False
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

    async def get_invite_info(self, token: str) -> InviteInfoResponse:
        """Valida o token de convite e retorna os metadados do condomínio e da unidade."""
        user = await self.repository.get_by_invite_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convite não encontrado ou inválido."
            )

        if user.token_convite_expira_em and user.token_convite_expira_em < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este convite de ativação expirou. Solicite ao síndico o reenvio do convite."
            )

        if user.status_cadastro == "ATIVO":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este convite já foi utilizado e a conta já se encontra ativa. Acesse com seu e-mail e senha."
            )

        condo_repo = CondominioRepository(self.db)
        condo = await condo_repo.get_by_id(user.condominio_id)
        condo_nome = condo.nome if condo else "Condomínio"
        condo_slug = condo.slug if condo else str(user.condominio_id)
        cor_primaria = condo.cor_primaria if (condo and condo.cor_primaria) else "#2563eb"
        cor_sidebar = condo.cor_sidebar if (condo and condo.cor_sidebar) else "#09090b"

        bloco = None
        numero = None
        if user.unidade_id:
            unit = await self.unit_repository.get_by_id(user.unidade_id)
            if unit:
                bloco = unit.bloco
                numero = unit.numero

        return InviteInfoResponse(
            token=token,
            nome=user.nome,
            email=user.email,
            tipo_usuario=user.tipo_usuario,
            condominio_id=user.condominio_id or 1,
            condominio_nome=condo_nome,
            condominio_slug=condo_slug,
            cor_primaria=cor_primaria,
            cor_sidebar=cor_sidebar,
            bloco=bloco,
            numero=numero
        )

    async def complete_invite(self, data: CompleteInviteRequest) -> TokenResponse:
        """Conclui o auto-cadastro do usuário convidado, define a senha pessoal e autentica imediatamente."""
        if data.senha != data.confirmacao_senha:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A senha e a confirmação de senha não coincidem."
            )

        user = await self.repository.get_by_invite_token(data.token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Convite não encontrado ou inválido."
            )

        if user.token_convite_expira_em and user.token_convite_expira_em < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este convite expirou. Solicite ao síndico o reenvio do link."
            )

        user.nome = data.nome_completo.strip()
        user.telefone = data.telefone.strip()
        if data.cpf:
            user.cpf = data.cpf.strip()
        user.senha_hash = get_password_hash(data.senha)
        user.status_cadastro = "ATIVO"
        user.ativo = True
        user.token_convite = None
        user.token_convite_expira_em = None
        user.precisa_trocar_senha = False

        updated = await self.repository.update(user)

        # Gera token JWT para login instantâneo com token_version
        access_token = create_access_token({
            "sub": str(updated.id),
            "email": updated.email,
            "tipo_usuario": updated.tipo_usuario,
            "condominio_id": updated.condominio_id,
            "token_version": getattr(updated, "token_version", 1) or 1
        })
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(updated)
        )

