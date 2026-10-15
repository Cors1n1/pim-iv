from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Unit
from app.repositories.unit_repository import UnitRepository
from app.repositories.user_repository import UserRepository
from app.schemas.unit import UnitCreate, UnitResponse, UnitUpdate


class UnitService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.unit_repo = UnitRepository(db)
        self.user_repo = UserRepository(db)

    async def list_units(self, include_inactive: bool = True) -> List[UnitResponse]:
        """Retorna lista de todas as unidades do condomínio."""
        units = await self.unit_repo.list_all(include_inactive=include_inactive)
        return [UnitResponse.model_validate(u) for u in units]

    async def get_unit(self, unit_id: int) -> UnitResponse:
        """Busca unidade por ID."""
        unit = await self.unit_repo.get_by_id(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada."
            )
        return UnitResponse.model_validate(unit)

    async def update_unit(self, unit_id: int, data: UnitUpdate) -> UnitResponse:
        """Atualiza informações da unidade, como status ativo/inativo."""
        unit = await self.unit_repo.get_by_id(unit_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada."
            )

        if data.bloco is not None:
            unit.bloco = data.bloco.strip()
        if data.numero is not None:
            unit.numero = data.numero.strip()
        if data.andar is not None:
            unit.andar = data.andar
        if data.ativo is not None:
            unit.ativo = data.ativo

        updated = await self.unit_repo.update(unit)
        return UnitResponse.model_validate(updated)

    async def create_unit(self, data: UnitCreate) -> UnitResponse:
        """Cadastra nova unidade após validar duplicidade de bloco e número."""
        existing = await self.unit_repo.get_by_bloco_numero(data.bloco, data.numero)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A unidade '{data.bloco} - {data.numero}' já está cadastrada."
            )

        new_unit = Unit(
            bloco=data.bloco.strip(),
            numero=data.numero.strip(),
            andar=data.andar,
            morador_responsavel_id=data.morador_responsavel_id
        )
        created = await self.unit_repo.create(new_unit)
        # Recarrega com relacionamentos
        return await self.get_unit(created.id)

    async def assign_resident(self, unit_id: int, user_id: Optional[int]) -> UnitResponse:
        """Vincula um morador existente à unidade."""
        if user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário morador não encontrado."
                )
            if user.tipo_usuario != "MORADOR":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Apenas usuários com perfil 'MORADOR' podem ser vinculados a uma unidade."
                )

        updated_unit = await self.unit_repo.assign_resident(unit_id, user_id)
        if not updated_unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada."
            )
        return await self.get_unit(updated_unit.id)
