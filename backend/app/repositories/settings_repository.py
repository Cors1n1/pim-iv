from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import CondoSettings, PlatformSettings


class SettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self, condominio_id: int = 1) -> CondoSettings:
        stmt = select(CondoSettings).filter(CondoSettings.condominio_id == condominio_id)
        result = await self.db.execute(stmt)
        settings = result.scalars().first()
        if not settings:
            # Cria registro inicial padrão se não existir para este condomínio
            settings = CondoSettings(condominio_id=condominio_id)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings

    async def update_settings(self, settings: CondoSettings) -> CondoSettings:
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings

    async def get_platform_settings(self) -> PlatformSettings:
        stmt = select(PlatformSettings).filter(PlatformSettings.id == 1)
        result = await self.db.execute(stmt)
        settings = result.scalars().first()
        if not settings:
            settings = PlatformSettings(id=1)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings

    async def update_platform_settings(self, settings: PlatformSettings) -> PlatformSettings:
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
