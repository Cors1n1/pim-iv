from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.settings_repository import SettingsRepository
from app.schemas.settings import CondoSettingsPublicResponse, CondoSettingsResponse, CondoSettingsUpdate


class SettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SettingsRepository(db)

    async def get_public_settings(self) -> CondoSettingsPublicResponse:
        settings = await self.repo.get_settings()
        return CondoSettingsPublicResponse.model_validate(settings)

    async def get_admin_settings(self, current_user: User) -> CondoSettingsResponse:
        if current_user.tipo_usuario not in ("ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso exclusivo para a administração ou síndico."
            )
        settings = await self.repo.get_settings()
        return CondoSettingsResponse.model_validate(settings)

    async def update_settings(self, current_user: User, data: CondoSettingsUpdate) -> CondoSettingsResponse:
        if current_user.tipo_usuario not in ("ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso exclusivo para a administração ou síndico."
            )

        settings = await self.repo.get_settings()

        if data.nome_condominio is not None:
            settings.nome_condominio = data.nome_condominio.strip()
        if data.endereco is not None:
            settings.endereco = data.endereco.strip() if data.endereco else None
        if data.telefone_portaria is not None:
            settings.telefone_portaria = data.telefone_portaria.strip() if data.telefone_portaria else None
        if data.email_contato is not None:
            settings.email_contato = data.email_contato.strip() if data.email_contato else None
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
        return CondoSettingsResponse.model_validate(updated)
