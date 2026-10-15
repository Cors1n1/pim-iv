from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.routers.deps import get_current_user, get_db, require_role
from app.schemas.user import ChangePasswordRequest, LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Autenticação & Usuários"])


@router.post("/login", response_model=TokenResponse, summary="Efetuar login no sistema")
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Realiza a autenticação de síndicos, porteiros ou condôminos,
    gerando o token JWT e gravando auditoria no banco de dados.
    """
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    service = AuthService(db)
    return await service.authenticate(
        login_data=payload,
        client_ip=client_ip,
        user_agent=user_agent
    )


@router.post("/register", response_model=UserResponse, summary="Cadastrar novo usuário")
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _current_admin: User = Depends(require_role(["ADMIN", "SINDICO"]))
) -> UserResponse:
    """
    Cadastra um novo usuário no condomínio.
    Apenas administradores e síndicos têm permissão para registrar novos usuários.
    """
    service = AuthService(db)
    return await service.register_new_user(payload)


@router.get("/me", response_model=UserResponse, summary="Obter dados do usuário logado")
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Retorna os dados do perfil autenticado pelo token JWT."""
    return UserResponse.model_validate(current_user)


@router.get("/users", response_model=List[UserResponse], summary="Listar todos os usuários")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _current_admin: User = Depends(require_role(["ADMIN", "SINDICO", "PORTARIA"]))
) -> List[UserResponse]:
    """Lista usuários cadastrados (para gestão do síndico e portaria)."""
    service = AuthService(db)
    users = await service.repository.list_all(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.post("/change-password", response_model=UserResponse, summary="Alterar senha do usuário autenticado")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Permite a troca de senha do usuário autenticado.
    Obrigatório no primeiro acesso de novos moradores.
    """
    service = AuthService(db)
    return await service.change_password(current_user.id, payload)

