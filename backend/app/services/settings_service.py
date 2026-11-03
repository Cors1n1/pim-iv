from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import (
    CondoSettingsPublicResponse,
    CondoSettingsResponse,
    CondoSettingsUpdate,
    PlatformSettingsResponse,
    PlatformSettingsUpdate,
)


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SettingsRepository(db)

    async def get_public_settings(
        self,
        condominio_id: Optional[int] = None,
        slug: Optional[str] = None
    ) -> CondoSettingsPublicResponse:
        from app.repositories.condominio_repository import CondominioRepository
        condo_repo = CondominioRepository(self.db)
        
        condo = None
        if slug:
            condo = await condo_repo.get_by_slug(slug)
        elif condominio_id:
            condo = await condo_repo.get_by_id(condominio_id)
            
        if not condo:
            # Fallback para o condomínio pioneiro
            condo = await condo_repo.get_by_id(1)

        active_condo_id = condo.id if condo else 1
        settings = await self.repo.get_settings(active_condo_id)
        platform_settings = await self.repo.get_platform_settings()

        data = {
            "condominio_id": active_condo_id,
            "slug": condo.slug if condo else "bela-vista",
            "nome_condominio": condo.nome if condo else settings.nome_condominio,
            "endereco": condo.endereco if condo else settings.endereco,
            "telefone_portaria": condo.telefone if condo else settings.telefone_portaria,
            "email_contato": condo.email_contato if condo else settings.email_contato,
            "cor_primaria": condo.cor_primaria if condo else "#2563eb",
            "cor_secundaria": condo.cor_secundaria if condo else "#1d4ed8",
            "cor_sidebar": getattr(condo, "cor_sidebar", None) or "#09090b",
            "cor_fundo": getattr(condo, "cor_fundo", None) or "AUTO",
            "logo_url": condo.logo_url if condo else None,
            "suporte_email": platform_settings.suporte_email,
            "suporte_telefone": platform_settings.suporte_telefone,
            "suporte_horario": platform_settings.suporte_horario,
            "titulo_regularizacao": platform_settings.titulo_regularizacao or "O que fazer para regularizar?",
            "mensagem_regularizacao": platform_settings.mensagem_regularizacao,
            "titulo_suspensao": platform_settings.titulo_suspensao or "Acesso ao Condomínio Suspenso",
            "subtitulo_suspensao": platform_settings.subtitulo_suspensao or "O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central.",
            "tipo_gestao": getattr(condo, "tipo_gestao", "AUTOGESTAO") or "AUTOGESTAO",
            "administradora_nome": getattr(condo, "administradora_nome", None),
        }
        return CondoSettingsPublicResponse.model_validate(data)

    async def get_platform_support_settings(self) -> PlatformSettingsResponse:
        settings = await self.repo.get_platform_settings()
        return PlatformSettingsResponse.model_validate(settings)

    async def update_platform_support_settings(self, payload: PlatformSettingsUpdate) -> PlatformSettingsResponse:
        settings = await self.repo.get_platform_settings()
        if payload.suporte_email is not None:
            settings.suporte_email = payload.suporte_email.strip()
        if payload.suporte_telefone is not None:
            settings.suporte_telefone = payload.suporte_telefone.strip()
        if payload.suporte_horario is not None:
            settings.suporte_horario = payload.suporte_horario.strip() if payload.suporte_horario else None
        if payload.titulo_regularizacao is not None:
            settings.titulo_regularizacao = payload.titulo_regularizacao.strip() if payload.titulo_regularizacao else "O que fazer para regularizar?"
        if payload.mensagem_regularizacao is not None:
            settings.mensagem_regularizacao = payload.mensagem_regularizacao.strip() if payload.mensagem_regularizacao else None
        if payload.titulo_suspensao is not None:
            settings.titulo_suspensao = payload.titulo_suspensao.strip() if payload.titulo_suspensao else None
        if payload.subtitulo_suspensao is not None:
            settings.subtitulo_suspensao = payload.subtitulo_suspensao.strip() if payload.subtitulo_suspensao else None

        updated = await self.repo.update_platform_settings(settings)
        return PlatformSettingsResponse.model_validate(updated)

    async def get_admin_settings(self, current_user: User) -> CondoSettingsResponse:
        condo_id = current_user.condominio_id or 1
        settings = await self.repo.get_settings(condo_id)
        from app.repositories.condominio_repository import CondominioRepository
        condo_repo = CondominioRepository(self.db)
        condo = await condo_repo.get_by_id(condo_id)

        data = {
            "id": settings.id,
            "condominio_id": condo_id,
            "nome_condominio": condo.nome if condo else settings.nome_condominio,
            "endereco": condo.endereco if condo else settings.endereco,
            "telefone_portaria": condo.telefone if condo else settings.telefone_portaria,
            "email_contato": condo.email_contato if condo else settings.email_contato,
            "cor_primaria": condo.cor_primaria if condo else "#2563eb",
            "cor_secundaria": condo.cor_secundaria if condo else "#1d4ed8",
            "cor_sidebar": getattr(condo, "cor_sidebar", None) or "#09090b",
            "cor_fundo": getattr(condo, "cor_fundo", None) or "AUTO",
            "logo_url": condo.logo_url if condo else None,
            "prazo_retomada_horas": settings.prazo_retomada_horas,
            "prazo_standby_horas": settings.prazo_standby_horas,
            "intervalo_padrao_dias": settings.intervalo_padrao_dias,
            "dias_penalidade_queima": settings.dias_penalidade_queima,
            "queima_prioridade_cancelamento": settings.queima_prioridade_cancelamento,
            "enviar_email_ativo": settings.enviar_email_ativo,
            "atualizado_em": settings.atualizado_em
        }
        return CondoSettingsResponse.model_validate(data)

    async def update_settings(self, current_user: User, data: CondoSettingsUpdate) -> CondoSettingsResponse:
        condo_id = current_user.condominio_id or 1
        settings = await self.repo.get_settings(condo_id)
        from app.repositories.condominio_repository import CondominioRepository
        condo_repo = CondominioRepository(self.db)
        condo = await condo_repo.get_by_id(condo_id)

        if condo:
            if data.nome_condominio is not None:
                condo.nome = data.nome_condominio.strip()
                settings.nome_condominio = condo.nome
            if data.endereco is not None:
                condo.endereco = data.endereco.strip() if data.endereco else None
                settings.endereco = condo.endereco
            if data.telefone_portaria is not None:
                condo.telefone = data.telefone_portaria.strip() if data.telefone_portaria else None
                settings.telefone_portaria = condo.telefone
            if data.email_contato is not None:
                condo.email_contato = data.email_contato.strip() if data.email_contato else None
                settings.email_contato = condo.email_contato
            if data.cor_primaria is not None:
                condo.cor_primaria = data.cor_primaria.strip()
            if data.cor_secundaria is not None:
                condo.cor_secundaria = data.cor_secundaria.strip()
            if data.cor_sidebar is not None:
                condo.cor_sidebar = data.cor_sidebar.strip()
            if data.cor_fundo is not None:
                condo.cor_fundo = data.cor_fundo.strip()
            if data.logo_url is not None:
                condo.logo_url = data.logo_url.strip() if data.logo_url else None
            await condo_repo.update(condo)

        if data.prazo_retomada_horas is not None:
            settings.prazo_retomada_horas = data.prazo_retomada_horas
        if data.prazo_standby_horas is not None:
            settings.prazo_standby_horas = data.prazo_standby_horas
        if data.intervalo_padrao_dias is not None:
            settings.intervalo_padrao_dias = data.intervalo_padrao_dias
        if data.dias_penalidade_queima is not None:
            settings.dias_penalidade_queima = data.dias_penalidade_queima
        if data.queima_prioridade_cancelamento is not None:
            settings.queima_prioridade_cancelamento = data.queima_prioridade_cancelamento
        if data.enviar_email_ativo is not None:
            settings.enviar_email_ativo = data.enviar_email_ativo

        updated = await self.repo.update_settings(settings)
        return await self.get_admin_settings(current_user)
