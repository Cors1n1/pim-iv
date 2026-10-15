from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import CondoSettings


class SettingsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_settings(self) -> CondoSettings:
        stmt = select(CondoSettings).filter(CondoSettings.id == 1)
        result = await self.db.execute(stmt)
        settings = result.scalars().first()
        if not settings:
            # Cria registro inicial padrão se não existir
            settings = CondoSettings(id=1)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings

    async def update_settings(self, settings: CondoSettings) -> CondoSettings:
        self.db.add(settings)
        await self.db.commit()
        await self.db.refresh(settings)
        return settings
