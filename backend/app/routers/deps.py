from typing import AsyncGenerator, Callable, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import decode_access_token, get_client_ip
from app.models.user import User
from app.repositories.condominio_repository import CondominioRepository
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db_session():
        yield session


async def verify_console_ip(request: Request) -> None:
    """
    Verifica se o IP de origem está na lista de IPs permitidos, caso configurado.
    Se a lista de IPs permitidos estiver preenchida (CONSOLE_ALLOWED_IPS ou SUPERADMIN_ALLOWED_IPS),
    requisições fora da lista são rejeitadas.
    """
    allowed_ips_str = (settings.CONSOLE_ALLOWED_IPS or settings.SUPERADMIN_ALLOWED_IPS).strip()
    if not allowed_ips_str:
        # Modo aberto para desenvolvimento/local
        return

    allowed_ips = [ip.strip() for ip in allowed_ips_str.split(",") if ip.strip()]
    client_ip = get_client_ip(request)

    if client_ip not in allowed_ips:
        # Retorna 404 propositalmente para não revelar que a rota administrativa sequer existe
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Página ou recurso não encontrado."
        )

# Alias para compatibilidade
verify_superadmin_ip = verify_console_ip


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Extrai e valida criptograficamente o usuário portador do token JWT.
    Verifica se o usuário está ativo e se o condomínio associado está com assinatura ativa.
    """
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial ausente no token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = await repo.get_by_id(int(user_id_str))
    if not user or not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inativo ou não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validação de versão de token para invalidação de sessões antigas:
    token_ver = payload.get("token_version")
    current_ver = getattr(user, "token_version", 1) or 1
    if token_ver is not None and token_ver != current_ver:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sessão revogada ou expirada. Por favor, realize login novamente.",
            headers={"WWW-Authenticate": "Bearer", "X-Session-Revoked": "true"},
        )

    # Suporte / Impersonação da Diretoria:
    is_impersonation = payload.get("is_impersonation", False)
    if is_impersonation:
        db.expunge(user)
        impersonated_condo_id = payload.get("condominio_id")
        if impersonated_condo_id:
            user.condominio_id = impersonated_condo_id
            user.tipo_usuario = payload.get("tipo_usuario", "SINDICO")

    # Se o usuário pertencer a um condomínio e não for DIRETORIA/SUPERADMIN, valida o status do condomínio
    if user.condominio_id and not is_impersonation and user.tipo_usuario not in ("DIRETORIA", "SUPERADMIN"):
        condo_repo = CondominioRepository(db)
        condo = await condo_repo.get_by_id(user.condominio_id)
        if not condo or condo.status != "ATIVO":
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

    return user


def get_current_tenant_id(current_user: User = Depends(get_current_user)) -> Optional[int]:
    """
    Extrai o ID do condomínio do contexto autenticado pelo JWT.
    Garante que as consultas operem estritamente dentro do condomínio do usuário.
    """
    if current_user.condominio_id:
        return current_user.condominio_id
    if current_user.tipo_usuario in ("DIRETORIA", "SUPERADMIN"):
        return None
    return current_user.condominio_id


def require_role(allowed_roles: List[str]) -> Callable:
    """Controle de acesso baseado em papéis (RBAC)."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.tipo_usuario in ("DIRETORIA", "SUPERADMIN"):
            return current_user
        # Se a rota permite SINDICO ou ADMIN, o SUBSINDICO também possui autorização de gestão operacional
        effective_roles = set(allowed_roles)
        if "SINDICO" in effective_roles or "ADMIN" in effective_roles:
            effective_roles.add("SUBSINDICO")
        if current_user.tipo_usuario not in effective_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso restrito. Perfis autorizados: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


async def require_diretoria(current_user: User = Depends(get_current_user)) -> User:
    """Exige perfil DIRETORIA ou SUPERADMIN exclusivo para a gestão da rede CondoHub."""
    if current_user.tipo_usuario not in ("DIRETORIA", "SUPERADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito ao Console da Diretoria CondoHub."
        )
    return current_user

# Alias para compatibilidade retroativa
require_superadmin = require_diretoria
