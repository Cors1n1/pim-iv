from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, decode_activation_token, get_client_ip, get_password_hash, slugify
from app.models.condominio import Condominio
from app.models.settings import CondoSettings
from app.models.user import AccessLog, User
from app.routers.deps import get_current_user, get_db, require_role
from app.schemas.condominio import SindicoActivationInfoResponse, SindicoCompleteActivationRequest
from app.schemas.user import (
    ChangePasswordRequest,
    CompleteInviteRequest,
    InviteInfoResponse,
    LoginRequest,
    ResetUserPasswordRequest,
    TokenResponse,
    UserCreate,
    UserResponse
)
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
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    condo_slug_header = request.headers.get("X-Condo-Slug")
    service = AuthService(db)
    return await service.authenticate(
        login_data=payload,
        client_ip=client_ip,
        user_agent=user_agent,
        condo_slug_header=condo_slug_header
    )


@router.post("/register", response_model=UserResponse, summary="Cadastrar novo usuário")
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(["ADMIN", "SINDICO", "SUPERADMIN"]))
) -> UserResponse:
    """
    Cadastra um novo usuário no condomínio.
    Apenas administradores, síndicos e o SuperAdmin têm permissão para registrar novos usuários.
    """
    service = AuthService(db)
    return await service.register_new_user(payload, default_condominio_id=current_admin.condominio_id)


@router.get("/me", response_model=UserResponse, summary="Obter dados do usuário logado")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Retorna os dados do perfil autenticado pelo token JWT com metadados do condomínio."""
    res = UserResponse.model_validate(current_user)
    if current_user.condominio_id:
        condo = await db.get(Condominio, current_user.condominio_id)
        if condo:
            res.condominio_nome = condo.nome
            res.condominio_slug = condo.slug
    return res


@router.get("/users", response_model=List[UserResponse], summary="Listar todos os usuários")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SINDICO", "PORTARIA", "SUPERADMIN"]))
) -> List[UserResponse]:
    """Lista usuários cadastrados no condomínio do operador."""
    service = AuthService(db)
    condo_id = current_user.condominio_id if current_user.tipo_usuario != "SUPERADMIN" else None
    users = await service.repository.list_by_condominio(condominio_id=condo_id, skip=skip, limit=limit)
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


@router.post("/users/{user_id}/reset-password", summary="Redefinir senha de morador pelo síndico ou admin")
async def reset_resident_password(
    user_id: int,
    payload: ResetUserPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "SINDICO", "SUPERADMIN"]))
) -> Dict[str, Any]:
    """
    Permite ao síndico ou administrador redefinir emergencialmente a senha de um morador
    do seu próprio condomínio, registrando auditoria e exigindo troca no próximo acesso.
    """
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    # Validação de condomínio do usuário:
    if current_user.tipo_usuario in ("SINDICO", "ADMIN", "SUBSINDICO") and user.condominio_id != current_user.condominio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Este usuário não pertence ao seu condomínio."
        )

    # Não permite síndico resetar outros síndicos ou superadministradores por esta rota
    if current_user.tipo_usuario in ("SINDICO", "SUBSINDICO") and user.tipo_usuario in ("SINDICO", "SUBSINDICO", "SUPERADMIN", "DIRETORIA") and user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operação restrita. Não é permitido redefinir a senha deste perfil."
        )

    user.senha_hash = get_password_hash(payload.nova_senha)
    user.precisa_trocar_senha = payload.precisa_trocar_senha if payload.precisa_trocar_senha is not None else True
    user.token_version = (getattr(user, "token_version", 1) or 1) + 1

    client_ip = get_client_ip(request)
    audit_log = AccessLog(
        condominio_id=user.condominio_id,
        usuario_id=user.id,
        email_informado=user.email,
        ip_origem=client_ip,
        user_agent=f"Portal Síndico: Senha resetada por {current_user.nome} ({current_user.tipo_usuario})",
        sucesso=True
    )
    db.add(audit_log)
    await db.commit()

    return {
        "success": True,
        "message": f"Senha do usuário {user.nome} ({user.email}) redefinida com sucesso.",
        "user_id": user.id,
        "email": user.email,
        "nome": user.nome
    }


@router.get("/activation-info", response_model=SindicoActivationInfoResponse, summary="Consultar dados para primeiro acesso do síndico")
async def get_activation_info(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> SindicoActivationInfoResponse:
    """Valida o token assinado e retorna os dados cadastrais do condomínio e do síndico."""
    payload = decode_activation_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link de ativação inválido ou expirado. Solicite um novo link ao administrador."
        )

    user_id = int(payload.get("sub", 0))
    condo_id = int(payload.get("condominio_id", 0))

    user = await db.get(User, user_id)
    if not user or user.condominio_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cadastro de gestor não encontrado ou inconsistente."
        )

    # Link de uso único: se o gestor já cadastrou sua senha definitiva, o link de ativação é invalidado
    if not user.precisa_trocar_senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este link de primeiro acesso já foi utilizado anteriormente. Sua conta já está ativada. Acesse o portal pelo login normal."
        )

    condo = await db.get(Condominio, condo_id)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    if user.tipo_usuario == "SUBSINDICO":
        papel_desc = "Subsíndico(a)"
    elif user.tipo_usuario == "ADMIN":
        papel_desc = "Gestor de Administradora"
    else:
        papel_desc = "Síndico Titular"

    return SindicoActivationInfoResponse(
        condominio_id=condo.id,
        condominio_nome=condo.nome,
        condominio_slug=condo.slug or "",
        condominio_logo=condo.logo_url,
        cor_primaria=condo.cor_primaria or "#2563eb",
        cor_secundaria=condo.cor_secundaria or "#1d4ed8",
        cor_sidebar=getattr(condo, "cor_sidebar", None) or "#09090b",
        sindico_nome=user.nome,
        sindico_email=user.email,
        tipo_usuario=user.tipo_usuario,
        papel_descricao=papel_desc
    )


@router.post("/complete-activation", response_model=TokenResponse, summary="Concluir ativação da conta do síndico ou administradora")

async def complete_activation(
    payload: SindicoCompleteActivationRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Define a nova senha pessoal do síndico, complementa dados cadastrais
    e autentica imediatamente retornando o token JWT.
    """
    token_data = decode_activation_token(payload.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link de ativação inválido ou expirado. Solicite um novo link ao administrador."
        )

    user_id = int(token_data.get("sub", 0))
    condo_id = int(token_data.get("condominio_id", 0))

    user = await db.get(User, user_id)
    if not user or user.condominio_id != condo_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cadastro de síndico não encontrado."
        )

    # Link de uso único: bloqueia se a conta já foi previamente ativada
    if not user.precisa_trocar_senha:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta conta já foi ativada anteriormente. Acesse o portal com seu e-mail e senha cadastrados."
        )

    condo = await db.get(Condominio, condo_id)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    # 1. Atualiza dados e senha do síndico
    user.nome = payload.nome_completo.strip()
    if payload.telefone and payload.telefone.strip():
        user.telefone = payload.telefone.strip()
    user.senha_hash = get_password_hash(payload.nova_senha)
    user.precisa_trocar_senha = False
    user.ativo = True

    # 2. Atualiza dados oficiais e definitivos do condomínio
    if payload.nome_condominio and payload.nome_condominio.strip():
        condo.nome = payload.nome_condominio.strip()

    if payload.slug and payload.slug.strip():
        new_slug = slugify(payload.slug.strip())
        stmt_slug = select(Condominio).where(Condominio.slug == new_slug, Condominio.id != condo_id)
        existing_slug = (await db.execute(stmt_slug)).scalars().first()
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O identificador de URL '/c/{new_slug}/' já está em uso por outro condomínio."
            )
        condo.slug = new_slug
    elif condo.nome:
        candidate_slug = slugify(condo.nome)
        stmt_slug = select(Condominio).where(Condominio.slug == candidate_slug, Condominio.id != condo_id)
        if not (await db.execute(stmt_slug)).scalars().first():
            condo.slug = candidate_slug

    if payload.cnpj and payload.cnpj.strip():
        clean_cnpj = payload.cnpj.strip()
        stmt_cnpj = select(Condominio).where(Condominio.cnpj == clean_cnpj, Condominio.id != condo_id)
        existing_cnpj = (await db.execute(stmt_cnpj)).scalars().first()
        if existing_cnpj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O CNPJ '{clean_cnpj}' já está cadastrado em outro condomínio."
            )
        condo.cnpj = clean_cnpj
    if payload.endereco and payload.endereco.strip():
        condo.endereco = payload.endereco.strip()
    if payload.telefone_portaria and payload.telefone_portaria.strip():
        condo.telefone = payload.telefone_portaria.strip()

    # Sincroniza CondoSettings com nome e contatos atualizados
    settings_stmt = select(CondoSettings).where(CondoSettings.condominio_id == condo_id)
    settings_res = await db.execute(settings_stmt)
    condo_settings = settings_res.scalars().first()
    if condo_settings:
        condo_settings.nome_condominio = condo.nome
        if condo.endereco:
            condo_settings.endereco = condo.endereco
        if condo.telefone:
            condo_settings.telefone_portaria = condo.telefone

    # 3. Auditoria de acesso seguro
    client_ip = get_client_ip(request)
    audit = AccessLog(
        condominio_id=condo.id,
        usuario_id=user.id,
        email_informado=user.email,
        ip_origem=client_ip,
        user_agent="Ativação e Definição de Senha Concluída pelo Síndico",
        sucesso=True
    )
    db.add(audit)

    await db.commit()
    await db.refresh(user)

    # 4. Gera token JWT de acesso
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "condominio_id": condo.id,
            "tipo_usuario": user.tipo_usuario,
            "token_version": getattr(user, "token_version", 1) or 1
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/invite/{token}", response_model=InviteInfoResponse, summary="Obter dados para auto-cadastro via convite")
async def get_invite_info(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> InviteInfoResponse:
    """Retorna os dados públicos da unidade e condomínio para o morador completar o cadastro."""
    service = AuthService(db)
    return await service.get_invite_info(token)


@router.post("/complete-invite", response_model=TokenResponse, summary="Concluir auto-cadastro de morador via convite")
async def complete_invite(
    payload: CompleteInviteRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Recebe a senha definitiva, telefone e nome do morador, ativando sua conta e logando imediatamente."""
    service = AuthService(db)
    return await service.complete_invite(payload)


@router.post("/logout-all", summary="Revogar todas as sessões ativas (Instant Kickout)")
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Incrementa atomicamente a versão do token do usuário atual (token_version),
    expulsando imediatamente todos os dispositivos, celulares e computadores conectados.
    """
    user = await db.get(User, current_user.id)
    if user:
        user.token_version = (getattr(user, "token_version", 1) or 1) + 1
        await db.commit()
    return {
        "success": True,
        "message": "Todas as sessões ativas foram desconectadas imediatamente com sucesso."
    }




