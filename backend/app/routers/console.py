from datetime import time
import logging
import re
import secrets
from typing import Any, Dict, List, Optional
import unicodedata
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

logger = logging.getLogger("console_router")


def slugify(text: str) -> str:
    """Gera slug limpo e amigável para URL a partir do nome do condomínio."""
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    cleaned = re.sub(r'[^\w\s-]', '', normalized).strip().lower()
    return re.sub(r'[-\s]+', '-', cleaned)

from sqlalchemy import select

from app.core.security import create_access_token, create_activation_token, get_client_ip, get_password_hash
from app.models.condominio import Condominio
from app.models.notice import Notice
from app.models.reservation import CommonArea
from app.models.settings import CondoSettings
from app.models.user import AccessLog, Unit, User
from app.repositories.audit_repository import AuditRepository
from app.repositories.condominio_repository import CondominioRepository
from app.repositories.user_repository import UserRepository
from app.routers.deps import get_db, require_diretoria, verify_console_ip
from app.schemas.audit import AuditLogResponse
from app.schemas.condominio import (
    CondominioCreate,
    CondominioResponse,
    CondominioStatusUpdate,
    CondominioUpdate,
    ResendInviteResponse,
    ResetSindicoPasswordRequest,
)
from app.services.email_service import EmailService
from app.schemas.settings import PlatformSettingsResponse, PlatformSettingsUpdate
from app.schemas.user import (
    BroadcastNoticeRequest,
    GlobalUserResponse,
    GlobalUserUpdate,
    LoginRequest,
    ResetUserPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.settings_service import SettingsService

router = APIRouter(
    prefix="/api/console",
    tags=["Console de Operações - Diretoria CondoHub"],
    dependencies=[Depends(verify_console_ip)]
)


@router.post("/auth/login", response_model=TokenResponse, summary="Login no Console da Diretoria")
async def console_login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Autenticação restrita e segura da Diretoria de Operações da CondoHub.
    Rejeita requisições sem privilégios master.
    """
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent")
    service = AuthService(db)
    return await service.authenticate_console_admin(
        login_data=payload,
        client_ip=client_ip,
        user_agent=user_agent
    )


@router.get("/metrics", summary="Dashboard de métricas executivas da rede")
async def get_console_metrics(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """Retorna estatísticas consolidadas de todos os condomínios, faturamento e volumetria."""
    repo = CondominioRepository(db)
    return await repo.get_saas_metrics()


@router.get("/condominios", response_model=List[CondominioResponse], summary="Listar condomínios da rede")
async def list_condominios(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> List[CondominioResponse]:
    """Lista todos os condomínios cadastrados na rede com dados de moradores e unidades."""
    repo = CondominioRepository(db)
    items = await repo.list_all(skip=skip, limit=limit)
    response = []
    for item in items:
        c = item["condominio"]
        data = {
            "id": c.id,
            "nome": c.nome,
            "slug": c.slug,
            "cnpj": c.cnpj,
            "endereco": c.endereco,
            "telefone": c.telefone,
            "email_contato": c.email_contato,
            "plano": c.plano,
            "limite_unidades": c.limite_unidades,
            "status": c.status,
            "motivo_bloqueio": c.motivo_bloqueio,
            "tipo_gestao": getattr(c, "tipo_gestao", "AUTOGESTAO") or "AUTOGESTAO",
            "administradora_nome": getattr(c, "administradora_nome", None),
            "administradora_email": getattr(c, "administradora_email", None),
            "administradora_id": item.get("administradora_id"),
            "administradora_ativo": item.get("administradora_ativo"),
            "cor_primaria": c.cor_primaria,
            "cor_secundaria": c.cor_secundaria,
            "cor_sidebar": getattr(c, "cor_sidebar", None) or "#09090b",
            "logo_url": c.logo_url,
            "criado_em": c.criado_em,
            "atualizado_em": c.atualizado_em,
            "total_unidades": item.get("total_unidades", 0),
            "total_moradores": item.get("total_moradores", 0),
            "total_porteiros": item.get("total_porteiros", 0),
            "total_encomendas_pendentes": item.get("total_encomendas_pendentes", 0),
            "total_ocorrencias_abertas": item.get("total_ocorrencias_abertas", 0),
            "total_reservas": item.get("total_reservas", 0),
            "total_areas_comuns": item.get("total_areas_comuns", 0),
            "sindico_id": item.get("sindico_id"),
            "sindico_nome": item.get("sindico_nome"),
            "sindico_email": item.get("sindico_email"),
            "sindico_telefone": item.get("sindico_telefone"),
            "sindico_ativo": item.get("sindico_ativo", True),
            "tem_subsindico": item.get("tem_subsindico", False),
            "subsindico_id": item.get("subsindico_id"),
            "subsindico_nome": item.get("subsindico_nome"),
            "subsindico_email": item.get("subsindico_email"),
            "subsindico_telefone": item.get("subsindico_telefone"),
            "subsindico_ativo": item.get("subsindico_ativo")
        }
        response.append(CondominioResponse.model_validate(data))
    return response


@router.post("/condominios", response_model=CondominioResponse, status_code=status.HTTP_201_CREATED, summary="Cadastrar novo condomínio")
async def create_condominio(
    payload: CondominioCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> CondominioResponse:
    """
    Cadastra um novo condomínio na rede.
    Cria automaticamente configurações, primeiro síndico e áreas comuns iniciais.
    Gera link seguro de auto-ativação para o síndico definir sua própria senha.
    """
    repo = CondominioRepository(db)
    user_repo = UserRepository(db)

    # 1. Validação prévia de e-mail do primeiro síndico e administradora (se compartilhada)
    clean_email = payload.sindico_email.lower().strip()
    existing_user = await user_repo.get_by_email(clean_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"O e-mail '{payload.sindico_email}' já está em uso na plataforma. Escolha outro e-mail para o síndico."
        )

    clean_adm_email = None
    if payload.tipo_gestao == "COMPARTILHADA":
        if not payload.administradora_nome or not payload.administradora_nome.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para Gestão Compartilhada, informe o nome da administradora ou gestor responsável."
            )
        if not payload.administradora_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para Gestão Compartilhada, informe o e-mail de ativação da administradora."
            )
        clean_adm_email = str(payload.administradora_email).lower().strip()
        if clean_adm_email == clean_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O e-mail da administradora não pode ser igual ao e-mail do síndico."
            )
        existing_adm = await user_repo.get_by_email(clean_adm_email)
        if existing_adm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O e-mail '{clean_adm_email}' da administradora já está em uso na plataforma."
            )

    # 1.1 Validação do Subsíndico (se selecionado na governança)
    clean_sub_email = None
    if payload.tem_subsindico or payload.subsindico_email or payload.subsindico_nome:
        if not payload.subsindico_nome or not payload.subsindico_nome.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para cadastrar o Subsíndico, informe seu nome completo."
            )
        if not payload.subsindico_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para cadastrar o Subsíndico, informe seu e-mail institucional para envio do convite de ativação."
            )
        clean_sub_email = str(payload.subsindico_email).lower().strip()
        if clean_sub_email == clean_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O e-mail do Subsíndico não pode ser igual ao e-mail do Síndico Titular."
            )
        if clean_adm_email and clean_sub_email == clean_adm_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O e-mail do Subsíndico não pode ser igual ao e-mail da Administradora."
            )
        existing_sub = await user_repo.get_by_email(clean_sub_email)
        if existing_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O e-mail '{clean_sub_email}' do Subsíndico já está em uso na plataforma."
            )

    # 2. Definição do Nome do Condomínio (se omitido, gera provisório amigável para onboarding)
    if payload.nome and payload.nome.strip():
        condo_nome = payload.nome.strip()
    else:
        condo_nome = f"Condomínio em Ativação ({payload.sindico_nome.strip()})"

    # 3. Validação e definição da URL Slug exclusiva
    if payload.slug and payload.slug.strip():
        condo_slug = slugify(payload.slug.strip())
        existing_slug = await repo.get_by_slug(condo_slug)
        if existing_slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A URL '/c/{condo_slug}/' já está em uso por outro condomínio. Escolha outro identificador de URL."
            )
    else:
        condo_slug = slugify(condo_nome)
        existing_slug = await repo.get_by_slug(condo_slug)
        if existing_slug:
            import random
            condo_slug = f"{condo_slug}-{random.randint(100, 999)}"

    # 4. Hash Criptográfico Seguro Inicial (Contas protegidas até a ativação pessoal de cada gestor)
    initial_hash = get_password_hash(secrets.token_urlsafe(32))

    # 5. Transação Atômica: Inserção de Condomínio + Configurações + Áreas Comuns + Síndico (+ Administradora + Subsíndico)
    activation_token = None
    activation_url = None
    adm_activation_token = None
    adm_activation_url = None
    new_admin = None
    sub_activation_token = None
    sub_activation_url = None
    new_subsindico = None

    try:
        new_condo = Condominio(
            nome=condo_nome,
            slug=condo_slug,
            cnpj=None,
            endereco=None,
            telefone=None,
            email_contato=clean_email,
            plano=payload.plano or "PADRAO",
            limite_unidades=payload.limite_unidades,
            status="ATIVO",
            tipo_gestao=payload.tipo_gestao or "AUTOGESTAO",
            administradora_nome=payload.administradora_nome.strip() if (payload.tipo_gestao == "COMPARTILHADA" and payload.administradora_nome) else None,
            administradora_email=clean_adm_email if payload.tipo_gestao == "COMPARTILHADA" else None,
            cor_primaria=payload.cor_primaria or "#2563eb",
            cor_secundaria=payload.cor_secundaria or "#1d4ed8",
            cor_sidebar=payload.cor_sidebar or "#09090b"
        )
        db.add(new_condo)
        await db.flush()

        # Cria configurações padrão de governança e contatos do condomínio
        settings_entry = CondoSettings(
            condominio_id=new_condo.id,
            nome_condominio=new_condo.nome,
            endereco="",
            telefone_portaria="",
            email_contato=clean_email
        )
        db.add(settings_entry)

        # Cria 2 áreas comuns iniciais padrão para facilitar o início da gestão
        area1 = CommonArea(
            condominio_id=new_condo.id,
            nome="Salão de Festas Principal",
            descricao="Espaço climatizado com mesas, cadeiras, cozinha e churrasqueira integrada.",
            capacidade_pessoas=60,
            taxa_limpeza=0.00,
            hora_inicio=time(8, 0),
            hora_fim=time(22, 0),
            ativo=True
        )
        area2 = CommonArea(
            condominio_id=new_condo.id,
            nome="Churrasqueira Gourmet",
            descricao="Área externa com churrasqueira a carvão, freezer e bancada de granito.",
            capacidade_pessoas=25,
            taxa_limpeza=0.00,
            hora_inicio=time(9, 0),
            hora_fim=time(22, 0),
            ativo=True
        )
        db.add(area1)
        db.add(area2)

        # Criação do primeiro síndico com flag de troca obrigatória de senha
        new_sindico = User(
            condominio_id=new_condo.id,
            nome=payload.sindico_nome.strip(),
            email=clean_email,
            senha_hash=initial_hash,
            tipo_usuario="SINDICO",
            telefone=payload.sindico_telefone,
            ativo=True,
            precisa_trocar_senha=True
        )
        db.add(new_sindico)
        await db.flush()

        # Gera token criptográfico de ativação válido por 7 dias para o Síndico
        activation_token = create_activation_token(
            user_id=new_sindico.id,
            condominio_id=new_condo.id,
            email=new_sindico.email,
            days=7,
            scope="sindico_activation"
        )
        base_url = str(request.base_url).rstrip("/")
        activation_url = f"{base_url}/c/{new_condo.slug}/ativar?token={activation_token}"

        # Se gestão compartilhada, cria o gestor da Administradora (Role: ADMIN)
        if payload.tipo_gestao == "COMPARTILHADA" and clean_adm_email:
            new_admin = User(
                condominio_id=new_condo.id,
                nome=payload.administradora_nome.strip(),
                email=clean_adm_email,
                senha_hash=get_password_hash(secrets.token_urlsafe(32)),
                tipo_usuario="ADMIN",
                telefone=payload.administradora_telefone,
                ativo=True,
                precisa_trocar_senha=True
            )
            db.add(new_admin)
            await db.flush()

            adm_activation_token = create_activation_token(
                user_id=new_admin.id,
                condominio_id=new_condo.id,
                email=new_admin.email,
                days=7,
                scope="admin_activation"
            )
            adm_activation_url = f"{base_url}/c/{new_condo.slug}/ativar?token={adm_activation_token}"

            # Disparo assíncrono para a Administradora
            try:
                await EmailService.send_administradora_activation_email(
                    to_email=new_admin.email,
                    gestor_nome=new_admin.nome,
                    condo_nome=new_condo.nome,
                    condo_slug=new_condo.slug,
                    activation_url=adm_activation_url
                )
            except Exception as mail_err:
                logger.warning(f"Aviso: Falha ao enviar e-mail de ativação da administradora: {mail_err}")

        # Se informado Subsíndico, cria o usuário com perfil SUBSINDICO e gera link de ativação
        if clean_sub_email:
            new_subsindico = User(
                condominio_id=new_condo.id,
                nome=payload.subsindico_nome.strip(),
                email=clean_sub_email,
                senha_hash=get_password_hash(secrets.token_urlsafe(32)),
                tipo_usuario="SUBSINDICO",
                telefone=payload.subsindico_telefone,
                ativo=True,
                precisa_trocar_senha=True
            )
            db.add(new_subsindico)
            await db.flush()

            sub_activation_token = create_activation_token(
                user_id=new_subsindico.id,
                condominio_id=new_condo.id,
                email=new_subsindico.email,
                days=7,
                scope="subsindico_activation"
            )
            sub_activation_url = f"{base_url}/c/{new_condo.slug}/ativar?token={sub_activation_token}"

            try:
                await EmailService.send_subsindico_activation_email(
                    to_email=new_subsindico.email,
                    subsindico_nome=new_subsindico.nome,
                    condo_nome=new_condo.nome,
                    condo_slug=new_condo.slug,
                    activation_url=sub_activation_url
                )
            except Exception as mail_err:
                logger.warning(f"Aviso: Não foi possível enviar e-mail de ativação do subsíndico: {mail_err}")

        # Publica aviso inicial de boas-vindas
        notice = Notice(
            condominio_id=new_condo.id,
            titulo="Bem-vindo ao Portal do Condomínio!",
            mensagem="Seja bem-vindo ao portal de gestão e governança digital. Aqui você acompanha comunicados oficiais, registra visitantes, gerencia encomendas e reservas.",
            categoria="GERAL",
            autor_id=new_sindico.id
        )
        db.add(notice)

        # Disparo assíncrono do e-mail de ativação segura para o síndico
        try:
            await EmailService.send_sindico_activation_email(
                to_email=new_sindico.email,
                sindico_nome=new_sindico.nome,
                condo_nome=new_condo.nome,
                condo_slug=new_condo.slug,
                activation_url=activation_url
            )
        except Exception as mail_err:
            logger.warning(f"Aviso: Não foi possível disparar e-mail de ativação do síndico: {mail_err}")

        await db.commit()
        await db.refresh(new_condo)
        saved_condo = new_condo
    except Exception:
        await db.rollback()
        raise

    counts = await repo.count_relations(saved_condo.id)
    return CondominioResponse.model_validate({
        "id": saved_condo.id,
        "nome": saved_condo.nome,
        "slug": saved_condo.slug,
        "cnpj": saved_condo.cnpj,
        "endereco": saved_condo.endereco,
        "telefone": saved_condo.telefone,
        "email_contato": saved_condo.email_contato,
        "plano": saved_condo.plano,
        "limite_unidades": saved_condo.limite_unidades,
        "status": saved_condo.status,
        "motivo_bloqueio": saved_condo.motivo_bloqueio,
        "tipo_gestao": saved_condo.tipo_gestao,
        "administradora_nome": saved_condo.administradora_nome,
        "administradora_email": saved_condo.administradora_email,
        "administradora_id": new_admin.id if new_admin else None,
        "administradora_ativo": new_admin.ativo if new_admin else None,
        "administradora_activation_token": adm_activation_token,
        "administradora_activation_url": adm_activation_url,
        "tem_subsindico": True if new_subsindico else False,
        "subsindico_id": new_subsindico.id if new_subsindico else None,
        "subsindico_nome": new_subsindico.nome if new_subsindico else None,
        "subsindico_email": new_subsindico.email if new_subsindico else None,
        "subsindico_telefone": new_subsindico.telefone if new_subsindico else None,
        "subsindico_ativo": new_subsindico.ativo if new_subsindico else None,
        "subsindico_activation_token": sub_activation_token,
        "subsindico_activation_url": sub_activation_url,
        "cor_primaria": saved_condo.cor_primaria,
        "cor_secundaria": saved_condo.cor_secundaria,
        "cor_sidebar": getattr(saved_condo, "cor_sidebar", None) or "#09090b",
        "logo_url": saved_condo.logo_url,
        "criado_em": saved_condo.criado_em,
        "atualizado_em": saved_condo.atualizado_em,
        "activation_token": activation_token,
        "activation_url": activation_url,
        "senha_provisoria": None,
        **counts
    })


@router.post("/condominios/{condominio_id}/resend-invite", response_model=ResendInviteResponse, summary="Reenviar convite de ativação para o síndico ou administradora")
async def resend_sindico_invite(
    condominio_id: int,
    request: Request,
    papel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> ResendInviteResponse:
    """Gera novo token de ativação seguro e reenvia o convite por e-mail para o síndico ou administradora."""
    repo = CondominioRepository(db)
    condo = await repo.get_by_id(condominio_id)
    if not condo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condomínio não encontrado.")

    target_role = (papel or "SINDICO").upper()
    if target_role not in ("SINDICO", "ADMIN", "SUBSINDICO"):
        target_role = "SINDICO"

    stmt = select(User).where(
        User.condominio_id == condominio_id,
        User.tipo_usuario == target_role
    ).order_by(User.id.asc()).limit(1)
    target_user = (await db.execute(stmt)).scalars().first()

    if not target_user:
        stmt_fallback = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario.in_(["SINDICO", "SUBSINDICO", "ADMIN"])
        ).order_by(User.id.asc()).limit(1)
        target_user = (await db.execute(stmt_fallback)).scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum gestor (síndico, subsíndico ou administradora) associado a este condomínio para envio de convite."
        )

    # Reativa a obrigatoriedade de ativação com senha e bloqueia hash temporário
    target_user.senha_hash = get_password_hash(secrets.token_urlsafe(32))
    target_user.precisa_trocar_senha = True
    await db.commit()

    if target_user.tipo_usuario == "SUBSINDICO":
        scope = "subsindico_activation"
        papel_rotulo = "Subsíndico(a)"
    elif target_user.tipo_usuario == "ADMIN":
        scope = "admin_activation"
        papel_rotulo = "Administradora"
    else:
        scope = "sindico_activation"
        papel_rotulo = "Síndico Titular"

    token = create_activation_token(user_id=target_user.id, condominio_id=condo.id, email=target_user.email, days=7, scope=scope)
    base_url = str(request.base_url).rstrip("/")
    activation_url = f"{base_url}/c/{condo.slug}/ativar?token={token}"

    try:
        if target_user.tipo_usuario == "SUBSINDICO":
            await EmailService.send_subsindico_activation_email(
                to_email=target_user.email,
                subsindico_nome=target_user.nome,
                condo_nome=condo.nome,
                condo_slug=condo.slug,
                activation_url=activation_url
            )
        elif target_user.tipo_usuario == "ADMIN":
            await EmailService.send_administradora_activation_email(
                to_email=target_user.email,
                gestor_nome=target_user.nome,
                condo_nome=condo.nome,
                condo_slug=condo.slug,
                activation_url=activation_url
            )
        else:
            await EmailService.send_sindico_activation_email(
                to_email=target_user.email,
                sindico_nome=target_user.nome,
                condo_nome=condo.nome,
                condo_slug=condo.slug,
                activation_url=activation_url
            )
    except Exception as exc:
        logger.warning(f"Erro ao reenviar e-mail de ativação: {exc}")

    return ResendInviteResponse(
        success=True,
        condominio_id=condominio_id,
        sindico_email=target_user.email,
        activation_token=token,
        activation_url=activation_url,
        senha_provisoria=None,
        message=f"Convite reenviado com sucesso para {target_user.email} ({papel_rotulo})."
    )


@router.get("/condominios/{condominio_id}", response_model=CondominioResponse, summary="Obter detalhes de um condomínio")
async def get_condominio(
    condominio_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> CondominioResponse:
    repo = CondominioRepository(db)
    condo = await repo.get_by_id(condominio_id)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    counts = await repo.count_relations(condominio_id)
    data = {
        "id": condo.id,
        "nome": condo.nome,
        "slug": condo.slug,
        "cnpj": condo.cnpj,
        "endereco": condo.endereco,
        "telefone": condo.telefone,
        "email_contato": condo.email_contato,
        "plano": condo.plano,
        "limite_unidades": condo.limite_unidades,
        "status": condo.status,
        "motivo_bloqueio": condo.motivo_bloqueio,
        "tipo_gestao": getattr(condo, "tipo_gestao", "AUTOGESTAO") or "AUTOGESTAO",
        "administradora_nome": getattr(condo, "administradora_nome", None),
        "administradora_email": getattr(condo, "administradora_email", None),
        "cor_primaria": condo.cor_primaria,
        "cor_secundaria": condo.cor_secundaria,
        "cor_sidebar": getattr(condo, "cor_sidebar", None) or "#09090b",
        "logo_url": condo.logo_url,
        "criado_em": condo.criado_em,
        "atualizado_em": condo.atualizado_em,
        **counts
    }
    return CondominioResponse.model_validate(data)


@router.put("/condominios/{condominio_id}", response_model=CondominioResponse, summary="Atualizar dados de um condomínio")
async def update_condominio(
    condominio_id: int,
    payload: CondominioUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> CondominioResponse:
    repo = CondominioRepository(db)
    user_repo = UserRepository(db)
    condo = await repo.get_by_id(condominio_id)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    update_dict = payload.model_dump(exclude_unset=True)

    # Separa dados do síndico e administradora dos dados do condomínio
    sindico_fields = ["sindico_nome", "sindico_email", "sindico_telefone", "sindico_senha"]
    sindico_data = {k: update_dict.pop(k) for k in sindico_fields if k in update_dict}

    adm_fields = ["administradora_nome", "administradora_email", "administradora_telefone"]
    adm_data = {k: update_dict.pop(k) for k in adm_fields if k in update_dict}

    sub_fields = ["tem_subsindico", "subsindico_nome", "subsindico_email", "subsindico_telefone", "subsindico_senha", "remover_subsindico"]
    sub_data = {k: update_dict.pop(k) for k in sub_fields if k in update_dict}

    old_tipo_gestao = condo.tipo_gestao or "AUTOGESTAO"
    new_tipo_gestao = update_dict.get("tipo_gestao", old_tipo_gestao)

    adm_activation_token = None
    adm_activation_url = None
    adm_user_obj = None
    sub_activation_token = None
    sub_activation_url = None

    if "cnpj" in update_dict and update_dict["cnpj"] != condo.cnpj:
        existing = await repo.get_by_cnpj(update_dict["cnpj"])
        if existing and existing.id != condo.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CNPJ já está cadastrado em outro condomínio."
            )

    if "slug" in update_dict:
        raw_slug = update_dict.get("slug")
        if raw_slug and str(raw_slug).strip():
            clean_slug = slugify(str(raw_slug).strip())
            if clean_slug != condo.slug:
                existing_slug = await repo.get_by_slug(clean_slug)
                if existing_slug and existing_slug.id != condo.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"A URL '/c/{clean_slug}/' já está em uso por outro condomínio."
                    )
                update_dict["slug"] = clean_slug
        else:
            update_dict.pop("slug", None)

    # 1. Transição / Migração ou Reversão de Governança
    if new_tipo_gestao == "COMPARTILHADA":
        adm_nome = (adm_data.get("administradora_nome") or condo.administradora_nome or "").strip()
        adm_email_raw = (adm_data.get("administradora_email") or condo.administradora_email or "").strip().lower()

        if not adm_nome:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para definir Gestão Compartilhada, informe o nome da administradora ou gestor parceiro."
            )
        if not adm_email_raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para definir Gestão Compartilhada, informe o e-mail institucional da administradora."
            )

        clean_adm_email = adm_email_raw
        if sindico_data.get("sindico_email") and clean_adm_email == sindico_data["sindico_email"].lower().strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O e-mail da administradora não pode ser igual ao e-mail do síndico."
            )

        condo.tipo_gestao = "COMPARTILHADA"
        condo.administradora_nome = adm_nome
        condo.administradora_email = clean_adm_email

        # Verifica se já existe um usuário ADMIN vinculado a este condomínio
        stmt_adm = select(User).where(User.condominio_id == condo.id, User.tipo_usuario == "ADMIN")
        existing_admin = (await db.execute(stmt_adm)).scalars().first()

        if existing_admin:
            existing_admin.nome = adm_nome
            existing_admin.email = clean_adm_email
            existing_admin.ativo = True
            if adm_data.get("administradora_telefone"):
                existing_admin.telefone = adm_data["administradora_telefone"]
            adm_user_obj = existing_admin
        else:
            other_user = await user_repo.get_by_email(clean_adm_email)
            if other_user and other_user.id != (existing_admin.id if existing_admin else None):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"O e-mail '{clean_adm_email}' já está em uso na plataforma."
                )

            initial_hash = get_password_hash(secrets.token_urlsafe(32))
            adm_user_obj = User(
                condominio_id=condo.id,
                nome=adm_nome,
                email=clean_adm_email,
                senha_hash=initial_hash,
                tipo_usuario="ADMIN",
                telefone=adm_data.get("administradora_telefone"),
                ativo=True,
                precisa_trocar_senha=True
            )
            db.add(adm_user_obj)
            await db.flush()

        # Se estava migrando de AUTOGESTAO para COMPARTILHADA, gera link e dispara e-mail de ativação
        if old_tipo_gestao == "AUTOGESTAO":
            adm_activation_token = create_activation_token(
                user_id=adm_user_obj.id,
                condominio_id=condo.id,
                email=adm_user_obj.email,
                days=7,
                scope="admin_activation"
            )
            base_url = str(request.base_url).rstrip("/")
            adm_activation_url = f"{base_url}/c/{condo.slug}/ativar?token={adm_activation_token}"

            try:
                await EmailService.send_administradora_activation_email(
                    to_email=adm_user_obj.email,
                    gestor_nome=adm_user_obj.nome,
                    condo_nome=condo.nome,
                    condo_slug=condo.slug,
                    activation_url=adm_activation_url
                )
            except Exception as mail_err:
                logger.warning(f"Aviso: Não foi possível enviar e-mail de ativação da administradora: {mail_err}")

            audit_repo = AuditRepository(db)
            await audit_repo.create_log(
                usuario_id=_admin.id,
                condominio_id=condo.id,
                acao="GOVERNANCA_MIGRADA_COMPARTILHADA",
                detalhes=f"Governança migrada para Gestão Compartilhada. Administradora '{adm_nome}' ({clean_adm_email}) vinculada.",
                ip_origem=get_client_ip(request)
            )

    elif new_tipo_gestao == "AUTOGESTAO":
        condo.tipo_gestao = "AUTOGESTAO"
        condo.administradora_nome = None
        condo.administradora_email = None
        if old_tipo_gestao == "COMPARTILHADA":
            # Reversão: desativa usuários ADMIN da administradora neste condomínio
            stmt_adms = select(User).where(User.condominio_id == condo.id, User.tipo_usuario == "ADMIN")
            adms = (await db.execute(stmt_adms)).scalars().all()
            for a in adms:
                a.ativo = False

            audit_repo = AuditRepository(db)
            await audit_repo.create_log(
                usuario_id=_admin.id,
                condominio_id=condo.id,
                acao="GOVERNANCA_REVERTIDA_AUTOGESTAO",
                detalhes=f"Governança revertida para Autogestão (Apenas Síndico). Acessos da Administradora '{condo.administradora_nome}' desativados.",
                ip_origem=get_client_ip(request)
            )

    for key, val in update_dict.items():
        setattr(condo, key, val)
    updated = await repo.update(condo)

    # Sincroniza tabela de configurações visuais
    stmt_set = select(CondoSettings).where(CondoSettings.condominio_id == condo.id)
    settings = (await db.execute(stmt_set)).scalars().first()
    if settings:
        if "nome" in update_dict:
            settings.nome_condominio = condo.nome
        if "endereco" in update_dict:
            settings.endereco = condo.endereco
        if "telefone" in update_dict:
            settings.telefone_portaria = condo.telefone
        if "email_contato" in update_dict:
            settings.email_contato = condo.email_contato
        await db.commit()
    else:
        new_settings = CondoSettings(
            condominio_id=condo.id,
            nome_condominio=condo.nome,
            endereco=condo.endereco,
            telefone_portaria=condo.telefone,
            email_contato=condo.email_contato
        )
        db.add(new_settings)
        await db.commit()

    # Atualiza Síndico vinculado caso campos tenham sido informados
    if sindico_data:
        stmt_sindico = select(User).where(
            User.condominio_id == condo.id,
            User.tipo_usuario == "SINDICO",
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        sindico = (await db.execute(stmt_sindico)).scalars().first()

        if sindico:
            if "sindico_nome" in sindico_data and sindico_data["sindico_nome"]:
                sindico.nome = sindico_data["sindico_nome"]
            if "sindico_email" in sindico_data and sindico_data["sindico_email"]:
                new_email = sindico_data["sindico_email"].lower().strip()
                if new_email != sindico.email:
                    check_user = await user_repo.get_by_email(new_email)
                    if check_user and check_user.id != sindico.id:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"O e-mail '{new_email}' já está em uso na plataforma."
                        )
                    sindico.email = new_email
            if "sindico_telefone" in sindico_data:
                sindico.telefone = sindico_data["sindico_telefone"]
            if "sindico_senha" in sindico_data and sindico_data["sindico_senha"]:
                sindico.senha_hash = get_password_hash(sindico_data["sindico_senha"])
                sindico.precisa_trocar_senha = False
        elif sindico_data.get("sindico_nome") and sindico_data.get("sindico_email"):
            new_email = sindico_data["sindico_email"].lower().strip()
            check_user = await user_repo.get_by_email(new_email)
            if check_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"O e-mail '{new_email}' já está em uso na plataforma."
                )
            new_s = User(
                condominio_id=condo.id,
                nome=sindico_data["sindico_nome"],
                email=new_email,
                senha_hash=get_password_hash(sindico_data.get("sindico_senha") or "Sindico@123"),
                tipo_usuario="SINDICO",
                telefone=sindico_data.get("sindico_telefone"),
                ativo=True,
                precisa_trocar_senha=False
            )
            db.add(new_s)
        await db.commit()

    # Atualiza ou gerencia Subsíndico vinculado
    if sub_data:
        stmt_sub = select(User).where(
            User.condominio_id == condo.id,
            User.tipo_usuario == "SUBSINDICO"
        ).order_by(User.id.asc()).limit(1)
        sub_user = (await db.execute(stmt_sub)).scalars().first()

        if sub_data.get("remover_subsindico") is True or (sub_data.get("tem_subsindico") is False and not sub_data.get("subsindico_email")):
            if sub_user:
                sub_user.ativo = False
                await db.commit()
        elif sub_data.get("tem_subsindico") is True or sub_data.get("subsindico_nome") or sub_data.get("subsindico_email"):
            if sub_user:
                if sub_data.get("subsindico_nome"):
                    sub_user.nome = sub_data["subsindico_nome"]
                if sub_data.get("subsindico_email"):
                    new_sub_email = sub_data["subsindico_email"].lower().strip()
                    if new_sub_email != sub_user.email:
                        check_user = await user_repo.get_by_email(new_sub_email)
                        if check_user and check_user.id != sub_user.id:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"O e-mail '{new_sub_email}' já está em uso na plataforma."
                            )
                        sub_user.email = new_sub_email
                if "subsindico_telefone" in sub_data:
                    sub_user.telefone = sub_data["subsindico_telefone"]
                if sub_data.get("subsindico_senha"):
                    sub_user.senha_hash = get_password_hash(sub_data["subsindico_senha"])
                    sub_user.precisa_trocar_senha = False
                sub_user.ativo = True
                await db.commit()
            elif sub_data.get("subsindico_nome") and sub_data.get("subsindico_email"):
                new_sub_email = sub_data["subsindico_email"].lower().strip()
                check_user = await user_repo.get_by_email(new_sub_email)
                if check_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"O e-mail '{new_sub_email}' já está em uso na plataforma."
                    )
                new_sub = User(
                    condominio_id=condo.id,
                    nome=sub_data["subsindico_nome"],
                    email=new_sub_email,
                    senha_hash=get_password_hash(sub_data.get("subsindico_senha") or secrets.token_urlsafe(32)),
                    tipo_usuario="SUBSINDICO",
                    telefone=sub_data.get("subsindico_telefone"),
                    ativo=True,
                    precisa_trocar_senha=True if not sub_data.get("subsindico_senha") else False
                )
                db.add(new_sub)
                await db.flush()

                if not sub_data.get("subsindico_senha"):
                    sub_activation_token = create_activation_token(
                        user_id=new_sub.id,
                        condominio_id=condo.id,
                        email=new_sub.email,
                        days=7,
                        scope="subsindico_activation"
                    )
                    base_url = str(request.base_url).rstrip("/")
                    sub_activation_url = f"{base_url}/c/{condo.slug}/ativar?token={sub_activation_token}"
                    try:
                        await EmailService.send_subsindico_activation_email(
                            to_email=new_sub.email,
                            subsindico_nome=new_sub.nome,
                            condo_nome=condo.nome,
                            condo_slug=condo.slug,
                            activation_url=sub_activation_url
                        )
                    except Exception as mail_err:
                        logger.warning(f"Aviso: Não foi possível enviar e-mail de ativação do subsíndico: {mail_err}")
                await db.commit()

    counts = await repo.count_relations(condominio_id)
    return CondominioResponse.model_validate({
        "id": updated.id,
        "nome": updated.nome,
        "slug": updated.slug,
        "cnpj": updated.cnpj,
        "endereco": updated.endereco,
        "telefone": updated.telefone,
        "email_contato": updated.email_contato,
        "plano": updated.plano,
        "limite_unidades": updated.limite_unidades,
        "status": updated.status,
        "motivo_bloqueio": updated.motivo_bloqueio,
        "tipo_gestao": getattr(updated, "tipo_gestao", "AUTOGESTAO") or "AUTOGESTAO",
        "administradora_nome": getattr(updated, "administradora_nome", None),
        "administradora_email": getattr(updated, "administradora_email", None),
        "administradora_id": adm_user_obj.id if adm_user_obj else None,
        "administradora_ativo": adm_user_obj.ativo if adm_user_obj else None,
        "administradora_activation_token": adm_activation_token,
        "administradora_activation_url": adm_activation_url,
        "subsindico_activation_token": sub_activation_token,
        "subsindico_activation_url": sub_activation_url,
        "cor_primaria": updated.cor_primaria,
        "cor_secundaria": updated.cor_secundaria,
        "cor_sidebar": getattr(updated, "cor_sidebar", None) or "#09090b",
        "logo_url": updated.logo_url,
        "criado_em": updated.criado_em,
        "atualizado_em": updated.atualizado_em,
        **counts
    })


@router.post("/condominios/{condominio_id}/reset-sindico-password", summary="Redefinir senha do síndico ou subsíndico responsável")
async def reset_sindico_password(
    condominio_id: int,
    payload: ResetSindicoPasswordRequest,
    papel: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """Permite ao Super Admin redefinir emergencialmente a senha do síndico ou subsíndico do condomínio."""
    target_role = (papel or "SINDICO").upper()
    if target_role == "SUBSINDICO":
        stmt = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "SUBSINDICO",
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        cargo_label = "subsíndico(a)"
    elif target_role == "ADMIN":
        stmt = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "ADMIN",
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        cargo_label = "gestor da administradora"
    else:
        stmt = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario.in_(["SINDICO", "ADMIN"]),
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        cargo_label = "síndico titular"

    gestor = (await db.execute(stmt)).scalars().first()
    if not gestor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum {cargo_label} ativo encontrado para este condomínio."
        )

    gestor.senha_hash = get_password_hash(payload.nova_senha)
    gestor.precisa_trocar_senha = False
    await db.commit()
    return {
        "success": True,
        "message": f"Senha de {gestor.nome} ({cargo_label}) redefinida com sucesso.",
        "sindico_email": gestor.email
    }


@router.get("/audit", response_model=List[AuditLogResponse], summary="Logs globais de auditoria da rede")
async def get_global_audit_logs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> List[AuditLogResponse]:
    """Retorna os registros de auditoria e conexões em tempo real de toda a plataforma."""
    audit_repo = AuditRepository(db)
    logs = await audit_repo.list_logs(condominio_id=None, limit=limit)
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.patch("/condominios/{condominio_id}/status", response_model=CondominioResponse, summary="Suspender ou Reativar Condomínio")
async def change_condominio_status(
    condominio_id: int,
    payload: CondominioStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> CondominioResponse:
    """
    Bloqueia ou reativa o acesso de um condomínio inteiro.
    Ao suspender, todo morador ou síndico é bloqueado ao tentar efetuar login.
    Nenhum dado é excluído; apenas o status de acesso é alterado para que a reativação seja imediata.
    """
    repo = CondominioRepository(db)
    condo = await repo.update_status(condominio_id, payload.status, payload.motivo)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    counts = await repo.count_relations(condominio_id)
    return CondominioResponse.model_validate({
        "id": condo.id,
        "nome": condo.nome,
        "slug": condo.slug,
        "cnpj": condo.cnpj,
        "endereco": condo.endereco,
        "telefone": condo.telefone,
        "email_contato": condo.email_contato,
        "plano": condo.plano,
        "limite_unidades": condo.limite_unidades,
        "status": condo.status,
        "motivo_bloqueio": condo.motivo_bloqueio,
        "cor_primaria": condo.cor_primaria,
        "cor_secundaria": condo.cor_secundaria,
        "cor_sidebar": getattr(condo, "cor_sidebar", None) or "#09090b",
        "logo_url": condo.logo_url,
        "criado_em": condo.criado_em,
        "atualizado_em": condo.atualizado_em,
        **counts
    })


@router.post("/condominios/{condominio_id}/impersonate", response_model=TokenResponse, summary="Acesso de suporte executivo ao condomínio")
async def impersonate_condominio(
    condominio_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_diretoria)
) -> TokenResponse:
    """
    Gera um token de acesso de suporte especial vinculado ao Condomínio X.
    Permite à Diretoria inspecionar a interface e prestar suporte técnico
    ao síndico do condomínio com permissões de auditoria.
    """
    repo = CondominioRepository(db)
    condo = await repo.get_by_id(condominio_id)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    token_data = {
        "sub": str(admin.id),
        "email": admin.email,
        "tipo_usuario": "SINDICO",
        "condominio_id": condo.id,
        "token_version": getattr(admin, "token_version", 1) or 1,
        "is_impersonation": True
    }
    access_token = create_access_token(data=token_data)

    user_response = UserResponse(
        id=admin.id,
        condominio_id=condo.id,
        condominio_nome=condo.nome,
        condominio_slug=condo.slug,
        nome=f"{admin.nome} [Suporte: {condo.nome}]",
        email=admin.email,
        telefone=admin.telefone,
        tipo_usuario="SINDICO",
        ativo=True,
        precisa_trocar_senha=False,
        token_version=getattr(admin, "token_version", 1) or 1,
        criado_em=admin.criado_em
    )
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@router.delete("/condominios/{condominio_id}", status_code=status.HTTP_200_OK, summary="Excluir condomínio e todos os seus dados")
async def delete_condominio(
    condominio_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """
    Exclui um condomínio e todos os seus dados associados permanentemente da plataforma.
    O condomínio ID 1 (matriz Residencial Bela Vista) é protegido e não pode ser excluído.
    """
    if condominio_id == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O condomínio matriz Residencial Bela Vista (ID: 1) é protegido e não pode ser excluído."
        )

    repo = CondominioRepository(db)
    condo = await repo.get_by_id(condominio_id)
    if not condo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Condomínio não encontrado."
        )

    nome_condo = condo.nome
    slug_condo = condo.slug

    success = await repo.delete_condominio_cascade(condominio_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao excluir condomínio."
        )

    audit_repo = AuditRepository(db)
    admin_exists = await db.get(User, admin.id) if admin else None
    await audit_repo.create_log(
        usuario_id=admin.id if admin_exists else None,
        condominio_id=None,
        acao="EXCLUSAO_CONDOMINIO",
        detalhes=f"Condomínio '{nome_condo}' (ID: {condominio_id}, slug: '{slug_condo}') foi excluído definitivamente da plataforma pela Diretoria.",
        ip_origem=get_client_ip(request),
        user_agent=request.headers.get("user-agent")
    )

    return {
        "status": "success",
        "message": f"Condomínio '{nome_condo}' excluído com sucesso."
    }


@router.get("/users", response_model=List[GlobalUserResponse], summary="Listar todos os usuários da rede")
async def list_global_users(
    skip: int = 0,
    limit: int = 300,
    q: Optional[str] = None,
    tipo: Optional[str] = None,
    condominio_id: Optional[int] = None,
    unidade: Optional[str] = None,
    status: Optional[str] = None,
    ativo: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> List[GlobalUserResponse]:
    """Retorna lista de usuários de todos os condomínios com busca e filtros operacionais."""
    stmt = (
        select(User, Condominio.nome.label("condo_nome"), Unit.bloco, Unit.numero)
        .outerjoin(Condominio, User.condominio_id == Condominio.id)
        .outerjoin(Unit, User.unidade_id == Unit.id)
    )

    if condominio_id:
        stmt = stmt.where(User.condominio_id == condominio_id)
    if tipo:
        stmt = stmt.where(User.tipo_usuario == tipo.upper())
    if status:
        if status.upper() == "ATIVO":
            stmt = stmt.where(User.ativo.is_(True))
        elif status.upper() == "BLOQUEADO":
            stmt = stmt.where(User.ativo.is_(False))
    elif ativo is not None:
        stmt = stmt.where(User.ativo == ativo)
    if unidade:
        u_pattern = f"%{unidade.strip()}%"
        stmt = stmt.where(
            (Unit.bloco.ilike(u_pattern)) |
            (Unit.numero.ilike(u_pattern))
        )
    if q:
        query_pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            (User.nome.ilike(query_pattern)) |
            (User.email.ilike(query_pattern)) |
            (User.telefone.ilike(query_pattern)) |
            (Condominio.nome.ilike(query_pattern)) |
            (Unit.bloco.ilike(query_pattern)) |
            (Unit.numero.ilike(query_pattern))
        )

    stmt = stmt.order_by(User.id.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    users_list = []
    for user, condo_nome, bloco, numero in rows:
        unidade_identificador = f"Bloco {bloco} - Apto {numero}" if bloco and numero else None
        users_list.append(GlobalUserResponse(
            id=user.id,
            condominio_id=user.condominio_id,
            condominio_nome=condo_nome or "Plataforma Geral",
            nome=user.nome,
            email=user.email,
            telefone=user.telefone,
            tipo_usuario=user.tipo_usuario,
            ativo=user.ativo,
            unidade_id=user.unidade_id,
            unidade_identificador=unidade_identificador,
            criado_em=user.criado_em
        ))

    return users_list


@router.post("/users/{user_id}/reset-password", summary="Redefinir senha de qualquer usuário da rede")
async def reset_global_user_password(
    user_id: int,
    payload: ResetUserPasswordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """Super Admin pode resetar a senha de acesso de qualquer usuário da rede (morador, porteiro ou síndico)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    user.senha_hash = get_password_hash(payload.nova_senha)
    user.precisa_trocar_senha = payload.precisa_trocar_senha if payload.precisa_trocar_senha is not None else False

    # Registra trilha de auditoria e conformidade LGPD
    client_ip = get_client_ip(request)
    audit_log = AccessLog(
        condominio_id=user.condominio_id,
        usuario_id=user.id,
        email_informado=user.email,
        ip_origem=client_ip,
        user_agent=f"Console SuperAdmin: Senha redefinida pelo operador {admin.nome} ({admin.email})",
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


@router.patch("/users/{user_id}/toggle-status", summary="Bloquear ou desbloquear usuário da rede")
async def toggle_global_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """Alterna o status ativo/bloqueado de um usuário em toda a rede."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    user.ativo = not user.ativo
    await db.commit()

    novo_status = "ATIVO" if user.ativo else "BLOQUEADO"
    return {
        "success": True,
        "message": f"Usuário {user.nome} agora está {novo_status}.",
        "user_id": user.id,
        "ativo": user.ativo
    }


@router.post("/broadcast", summary="Disparar comunicado oficial em massa para condomínios")
async def broadcast_notice(
    payload: BroadcastNoticeRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """
    Publica um comunicado master nos condomínios.
    Se condominio_id for None, publica para TODOS os condomínios cadastrados na rede com batch_id único.
    """
    if payload.condominio_id:
        target_ids = [payload.condominio_id]
        batch_id = None
    else:
        result = await db.execute(select(Condominio.id).where(Condominio.status == "ATIVO"))
        target_ids = result.scalars().all()
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"

    if not target_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum condomínio ativo encontrado para broadcast.")

    for c_id in target_ids:
        notice = Notice(
            condominio_id=c_id,
            titulo=payload.titulo,
            mensagem=payload.mensagem,
            categoria=payload.categoria,
            autor_id=admin.id,
            ativo=True,
            batch_id=batch_id
        )
        db.add(notice)

    await db.commit()

    return {
        "success": True,
        "message": f"Comunicado transmitido com sucesso para {len(target_ids)} condomínio(s).",
        "condominios_afetados": len(target_ids),
        "batch_id": batch_id
    }


@router.get("/broadcasts", summary="Listar histórico de comunicados master transmitidos")
async def list_console_broadcasts(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> List[Dict[str, Any]]:
    """
    Retorna o histórico consolidado de avisos transmitidos pela Central Master,
    agrupando por lote (batch_id) ou por aviso individual direcionado.
    """
    stmt = (
        select(Notice)
        .options(joinedload(Notice.condominio), joinedload(Notice.autor))
        .order_by(Notice.criado_em.desc())
    )
    result = await db.execute(stmt)
    all_notices = result.scalars().all()

    broadcasts_map: Dict[str, Dict[str, Any]] = {}
    for n in all_notices:
        # Considera broadcast se tiver batch_id ou se o autor for ADMIN ou se foi emitido pelo painel
        group_key = n.batch_id if n.batch_id else f"single_{n.id}"
        if group_key not in broadcasts_map:
            is_global = bool(n.batch_id)
            condo_nome = "Todos os Condomínios (Rede Geral)" if is_global else (n.condominio.nome if n.condominio else f"Condomínio #{n.condominio_id}")
            broadcasts_map[group_key] = {
                "id": n.id,
                "batch_id": n.batch_id,
                "group_key": group_key,
                "titulo": n.titulo,
                "mensagem": n.mensagem,
                "categoria": n.categoria,
                "criado_em": n.criado_em.isoformat() if n.criado_em else None,
                "ativo": n.ativo,
                "destino_tipo": "TODOS" if is_global else "ESPECIFICO",
                "destino_nome": condo_nome,
                "total_condominios": 1,
                "condominio_id": n.condominio_id if not is_global else None
            }
        else:
            broadcasts_map[group_key]["total_condominios"] += 1

    return list(broadcasts_map.values())


@router.patch("/broadcasts/{group_key}/toggle-visibility", summary="Alternar visibilidade do comunicado no mural dos clientes")
async def toggle_broadcast_visibility(
    group_key: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """
    Oculta ou reexibe um comunicado no mural dos clientes sem removê-lo do histórico master.
    """
    if group_key.startswith("batch_"):
        result = await db.execute(select(Notice).where(Notice.batch_id == group_key))
    elif group_key.startswith("single_"):
        notice_id = int(group_key.replace("single_", ""))
        result = await db.execute(select(Notice).where(Notice.id == notice_id))
    elif group_key.isdigit():
        result = await db.execute(select(Notice).where(Notice.id == int(group_key)))
    else:
        result = await db.execute(select(Notice).where(Notice.batch_id == group_key))

    notices = result.scalars().all()
    if not notices:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comunicado não encontrado.")

    new_ativo = not notices[0].ativo
    for n in notices:
        n.ativo = new_ativo

    await db.commit()

    return {
        "success": True,
        "ativo": new_ativo,
        "message": "Comunicado visível no mural dos clientes." if new_ativo else "Comunicado ocultado do mural dos clientes (mantido no seu histórico master).",
        "total_afetados": len(notices)
    }


@router.delete("/broadcasts/{group_key}", summary="Excluir comunicado master definitivamente")
async def delete_console_broadcast(
    group_key: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> Dict[str, Any]:
    """Exclui definitivamente um comunicado do mural e do histórico."""
    if group_key.startswith("batch_"):
        result = await db.execute(select(Notice).where(Notice.batch_id == group_key))
    elif group_key.startswith("single_"):
        notice_id = int(group_key.replace("single_", ""))
        result = await db.execute(select(Notice).where(Notice.id == notice_id))
    elif group_key.isdigit():
        result = await db.execute(select(Notice).where(Notice.id == int(group_key)))
    else:
        result = await db.execute(select(Notice).where(Notice.batch_id == group_key))

    notices = result.scalars().all()
    if not notices:
        return {
            "success": True,
            "message": "Comunicado removido com sucesso."
        }

    count = len(notices)
    for n in notices:
        await db.delete(n)
    await db.commit()

    return {
        "success": True,
        "message": f"{count} comunicado(s) excluído(s) definitivamente."
    }


@router.get("/support-settings", response_model=PlatformSettingsResponse, summary="Obter canais de suporte da plataforma")
async def get_console_support_settings(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> PlatformSettingsResponse:
    """Retorna os dados oficiais de atendimento da plataforma exibidos aos síndicos em avisos de suspensão."""
    service = SettingsService(db)
    return await service.get_platform_support_settings()


@router.put("/support-settings", response_model=PlatformSettingsResponse, summary="Atualizar canais de suporte da plataforma")
async def update_console_support_settings(
    payload: PlatformSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_diretoria)
) -> PlatformSettingsResponse:
    """Atualiza o e-mail, telefone/WhatsApp e orientações de suporte exibidas aos síndicos."""
    service = SettingsService(db)
    return await service.update_platform_support_settings(payload)

