import asyncio
from datetime import datetime, timedelta, timezone
import secrets
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import Unit, User
from app.repositories.condominio_repository import CondominioRepository
from app.repositories.unit_repository import UnitRepository
from app.repositories.user_repository import UserRepository
from app.schemas.unit import (
    InviteResidentRequest,
    UnitBatchCreate,
    UnitBatchResponse,
    UnitCreate,
    UnitOverviewResponse,
    UnitResponse,
    UnitUpdate
)
from app.services.email_service import EmailService


class UnitService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.unit_repo = UnitRepository(db)
        self.user_repo = UserRepository(db)
        self.condo_repo = CondominioRepository(db)

    async def list_units(
        self,
        condominio_id: Optional[int] = None,
        include_inactive: bool = True
    ) -> List[UnitResponse]:
        """Retorna lista de todas as unidades do condomínio especificado."""
        units = await self.unit_repo.list_all(condominio_id=condominio_id, include_inactive=include_inactive)
        return [UnitResponse.model_validate(u) for u in units]

    async def get_unit(self, unit_id: int, condominio_id: Optional[int] = None) -> UnitResponse:
        """Busca unidade por ID com validação de tenant."""
        unit = await self.unit_repo.get_by_id(unit_id, condominio_id=condominio_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada ou não pertence ao seu condomínio."
            )
        return UnitResponse.model_validate(unit)

    async def update_unit(
        self,
        unit_id: int,
        data: UnitUpdate,
        condominio_id: Optional[int] = None
    ) -> UnitResponse:
        """Atualiza informações da unidade com proteção multi-tenant."""
        unit = await self.unit_repo.get_by_id(unit_id, condominio_id=condominio_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada ou não pertence ao seu condomínio."
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

    async def create_unit(self, data: UnitCreate, condominio_id: int) -> UnitResponse:
        """Cadastra nova unidade após validar duplicidade e o teto do plano contratado."""
        condo = await self.condo_repo.get_by_id(condominio_id)
        if condo and condo.limite_unidades:
            total_cadastradas = await self.unit_repo.count(condominio_id=condominio_id)
            if total_cadastradas >= condo.limite_unidades:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Limite contratado de {condo.limite_unidades} unidades atingido. Entre em contato com a administração da rede para expandir a capacidade do condomínio."
                )

        existing = await self.unit_repo.get_by_bloco_numero(data.bloco, data.numero, condominio_id=condominio_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A unidade '{data.bloco} - {data.numero}' já está cadastrada neste condomínio."
            )

        new_unit = Unit(
            condominio_id=condominio_id,
            bloco=data.bloco.strip(),
            numero=data.numero.strip(),
            andar=data.andar,
            morador_responsavel_id=data.morador_responsavel_id
        )
        created = await self.unit_repo.create(new_unit)
        return await self.get_unit(created.id, condominio_id=condominio_id)

    async def create_units_batch(self, condominio_id: int, data: UnitBatchCreate) -> UnitBatchResponse:
        """Gera automaticamente blocos de apartamentos e andares em lote com proteção anti-duplicação."""
        condo = await self.condo_repo.get_by_id(condominio_id)
        bloco_clean = data.bloco.strip()

        # Busca unidades existentes para detecção veloz em memória
        existing_units = await self.unit_repo.list_all(condominio_id=condominio_id, include_inactive=True)
        existing_keys = {(u.bloco.strip().upper(), u.numero.strip().upper()) for u in existing_units}

        novas_unidades: List[Unit] = []
        total_duplicados = 0

        for andar in range(data.andar_inicial, data.andar_final + 1):
            for apto_idx in range(1, data.aptos_por_andar + 1):
                if data.formato_numeracao.upper() == "DEZENA":
                    numero = f"{andar}{apto_idx}"
                else:  # CENTENA padrão predial (101, 102...)
                    numero = f"{andar}{apto_idx:02d}"

                key = (bloco_clean.upper(), numero.upper())
                if key in existing_keys:
                    total_duplicados += 1
                    continue

                new_unit = Unit(
                    condominio_id=condominio_id,
                    bloco=bloco_clean,
                    numero=numero,
                    andar=andar,
                    ativo=True
                )
                novas_unidades.append(new_unit)
                existing_keys.add(key)

        # Valida teto contratado do plano
        if condo and condo.limite_unidades:
            if len(existing_units) + len(novas_unidades) > condo.limite_unidades:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"A criação de {len(novas_unidades)} unidades ultrapassaria o limite contratado de {condo.limite_unidades} unidades deste condomínio."
                )

        # Inserção em lote
        for unit in novas_unidades:
            self.db.add(unit)
        if novas_unidades:
            await self.db.commit()
            for unit in novas_unidades:
                await self.db.refresh(unit)

        return UnitBatchResponse(
            total_criados=len(novas_unidades),
            total_duplicados=total_duplicados,
            unidades=[UnitResponse.model_validate(u) for u in novas_unidades]
        )

    async def invite_resident(
        self,
        unit_id: int,
        condominio_id: int,
        data: InviteResidentRequest
    ) -> UnitResponse:
        """Cadastra o morador com status 'PENDENTE_ATIVACAO' e despacha convite de auto-cadastro por e-mail."""
        unit = await self.unit_repo.get_by_id(unit_id, condominio_id=condominio_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada ou não pertence ao seu condomínio."
            )

        email_clean = data.email.strip().lower()
        nome_clean = data.nome.strip()

        token = secrets.token_urlsafe(32)
        expira_em = datetime.now(timezone.utc) + timedelta(days=7)

        existing_user = await self.user_repo.get_by_email(email_clean)
        if existing_user:
            if existing_user.condominio_id != condominio_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Este e-mail já está associado a outro condomínio no sistema."
                )
            existing_user.unidade_id = unit.id
            if existing_user.status_cadastro != "ATIVO":
                existing_user.status_cadastro = "PENDENTE_ATIVACAO"
                existing_user.token_convite = token
                existing_user.token_convite_expira_em = expira_em
            target_user = await self.user_repo.update(existing_user)
        else:
            random_temp_pwd = get_password_hash(secrets.token_hex(16))
            new_user = User(
                condominio_id=condominio_id,
                unidade_id=unit.id,
                nome=nome_clean,
                email=email_clean,
                senha_hash=random_temp_pwd,
                tipo_usuario=data.tipo_usuario,
                ativo=True,
                precisa_trocar_senha=False,
                status_cadastro="PENDENTE_ATIVACAO",
                token_convite=token,
                token_convite_expira_em=expira_em
            )
            target_user = await self.user_repo.create(new_user)

        await self.unit_repo.assign_resident(unit.id, target_user.id)

        # Envia e-mail oficial de convite
        condo = await self.condo_repo.get_by_id(condominio_id)
        condo_nome = condo.nome if condo else "Condomínio"
        condo_slug = condo.slug if (condo and condo.slug) else str(condominio_id)
        unit_desc = f"{unit.bloco} - Apto {unit.numero}"
        activation_url = f"http://localhost:8000/c/{condo_slug}/ativar-morador?token={token}"

        asyncio.create_task(
            EmailService.send_resident_invitation(
                to_email=email_clean,
                resident_name=nome_clean,
                condo_nome=condo_nome,
                unit_desc=unit_desc,
                activation_url=activation_url,
                tipo_usuario=data.tipo_usuario
            )
        )

        return await self.get_unit(unit.id, condominio_id=condominio_id)

    async def resend_invite(
        self,
        unit_id: int,
        condominio_id: int
    ) -> UnitResponse:
        """Reenvia o e-mail de convite para o morador pendente com novo token seguro."""
        unit = await self.unit_repo.get_by_id(unit_id, condominio_id=condominio_id)
        if not unit or not unit.morador_responsavel_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Esta unidade não possui morador associado para reenviar convite."
            )

        user = await self.user_repo.get_by_id(unit.morador_responsavel_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Morador não encontrado.")

        token = secrets.token_urlsafe(32)
        user.token_convite = token
        user.token_convite_expira_em = datetime.now(timezone.utc) + timedelta(days=7)
        user.status_cadastro = "PENDENTE_ATIVACAO"
        await self.user_repo.update(user)

        condo = await self.condo_repo.get_by_id(condominio_id)
        condo_nome = condo.nome if condo else "Condomínio"
        condo_slug = condo.slug if (condo and condo.slug) else str(condominio_id)
        unit_desc = f"{unit.bloco} - Apto {unit.numero}"
        activation_url = f"http://localhost:8000/c/{condo_slug}/ativar-morador?token={token}"

        asyncio.create_task(
            EmailService.send_resident_invitation(
                to_email=user.email,
                resident_name=user.nome,
                condo_nome=condo_nome,
                unit_desc=unit_desc,
                activation_url=activation_url,
                tipo_usuario=user.tipo_usuario
            )
        )

        return await self.get_unit(unit.id, condominio_id=condominio_id)

    async def assign_resident(
        self,
        unit_id: int,
        user_id: Optional[int],
        condominio_id: Optional[int] = None
    ) -> UnitResponse:
        """Vincula um morador existente à unidade com validação de condomínio."""
        unit = await self.unit_repo.get_by_id(unit_id, condominio_id=condominio_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada ou não pertence ao seu condomínio."
            )

        if user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário morador não encontrado."
                )
            if condominio_id is not None and user.condominio_id != condominio_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="O morador selecionado pertence a outro condomínio."
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
        return await self.get_unit(updated_unit.id, condominio_id=condominio_id)

    async def _build_unit_overview(self, unit: Unit) -> UnitOverviewResponse:
        """Monta o resumo consolidado da unidade com morador, encomendas e visitantes de hoje."""
        from datetime import date
        from sqlalchemy import select
        from app.models.delivery import Delivery
        from app.models.visitor import Visitor
        from app.schemas.unit import ResidentBrief, UnitDeliveryBrief, UnitVisitorBrief

        # 1. Encomendas pendentes
        stmt_del = (
            select(Delivery)
            .where(
                Delivery.unidade_id == unit.id,
                Delivery.status == "AGUARDANDO_RETIRADA"
            )
            .order_by(Delivery.data_chegada.desc())
        )
        res_del = await self.db.execute(stmt_del)
        deliveries = list(res_del.scalars().all())

        # 2. Visitantes de hoje ou que estão no condomínio
        today = date.today()
        stmt_vis = (
            select(Visitor)
            .where(
                Visitor.unidade_id == unit.id,
                (Visitor.data_prevista == today) | (Visitor.status == "NO_LOCAL")
            )
            .order_by(Visitor.criado_em.desc())
        )
        res_vis = await self.db.execute(stmt_vis)
        visitors = list(res_vis.scalars().all())

        morador_brief = None
        if unit.morador_responsavel:
            morador_brief = ResidentBrief.model_validate(unit.morador_responsavel)

        return UnitOverviewResponse(
            id=unit.id,
            bloco=unit.bloco,
            numero=unit.numero,
            andar=unit.andar,
            ativo=unit.ativo,
            morador=morador_brief,
            encomendas_pendentes=[UnitDeliveryBrief.model_validate(d) for d in deliveries],
            visitantes_hoje=[UnitVisitorBrief.model_validate(v) for v in visitors]
        )

    async def quick_lookup(self, condominio_id: int, query: str) -> List[UnitOverviewResponse]:
        """Busca rápida para guarita por bloco, número ou nome do morador."""
        units = await self.unit_repo.search_units(condominio_id=condominio_id, query=query, limit=20)
        return [await self._build_unit_overview(u) for u in units]

    async def get_unit_overview(self, unit_id: int, condominio_id: Optional[int] = None) -> UnitOverviewResponse:
        """Retorna o raio-x consolidado de uma unidade específica."""
        unit = await self.unit_repo.get_by_id(unit_id, condominio_id=condominio_id)
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unidade não encontrada ou não pertence ao seu condomínio."
            )
        return await self._build_unit_overview(unit)


