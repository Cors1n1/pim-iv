from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reservation import CommonArea, Reservation


class ReservationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_areas(self, include_inactive: bool = False) -> List[CommonArea]:
        """Lista todas as áreas comuns do condomínio."""
        stmt = select(CommonArea)
        if not include_inactive:
            stmt = stmt.where(CommonArea.ativo == True)
        stmt = stmt.order_by(CommonArea.nome)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_area_by_id(self, area_id: int) -> Optional[CommonArea]:
        """Busca área comum por ID."""
        stmt = select(CommonArea).where(CommonArea.id == area_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create_area(self, area: CommonArea) -> CommonArea:
        """Cadastra nova área comum."""
        self.db.add(area)
        await self.db.commit()
        await self.db.refresh(area)
        return area

    async def update_area(self, area: CommonArea) -> CommonArea:
        """Salva alterações em uma área comum."""
        await self.db.commit()
        await self.db.refresh(area)
        return area

    async def list_reservations(self) -> List[Reservation]:
        """Lista todas as reservas com relacionamentos de área, morador e unidade."""
        stmt = (
            select(Reservation)
            .options(
                selectinload(Reservation.area_comum),
                selectinload(Reservation.usuario),
                selectinload(Reservation.unidade)
            )
            .order_by(Reservation.data_reserva.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, reservation_id: int) -> Optional[Reservation]:
        """Busca reserva específica por ID."""
        stmt = (
            select(Reservation)
            .options(
                selectinload(Reservation.area_comum),
                selectinload(Reservation.usuario),
                selectinload(Reservation.unidade)
            )
            .where(Reservation.id == reservation_id)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, reservation: Reservation) -> Reservation:
        """Persiste nova reserva no banco de dados."""
        self.db.add(reservation)
        await self.db.commit()
        await self.db.refresh(reservation)
        return reservation

    async def cancel(self, reservation_id: int) -> Optional[Reservation]:
        """Cancela uma reserva existente."""
        res = await self.get_by_id(reservation_id)
        if not res:
            return None
        res.status = "CANCELADA"
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def handover_key(self, reservation_id: int, porteiro_id: int, entregue_para: str) -> Optional[Reservation]:
        """Registra a entrega da chave do espaço comum pela portaria."""
        from datetime import datetime, timezone
        res = await self.get_by_id(reservation_id)
        if not res:
            return None
        res.chave_entregue = True
        res.chave_entregue_por = porteiro_id
        res.chave_entregue_para = entregue_para
        res.chave_entregue_em = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def return_key(self, reservation_id: int) -> Optional[Reservation]:
        """Registra a devolução da chave do espaço comum na portaria."""
        from datetime import datetime, timezone
        res = await self.get_by_id(reservation_id)
        if not res:
            return None
        res.chave_devolvida = True
        res.chave_devolvida_em = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def get_last_reservation_of_unit(self, area_id: int, unit_id: Optional[int], before_date: "date", user_id: Optional[int] = None) -> Optional[Reservation]:
        """Busca a reserva mais recente da mesma unidade ou usuário nesta área comum (antes de uma data), considerando também prioridade queimada."""
        from sqlalchemy import or_
        conds = []
        if unit_id:
            conds.append(Reservation.unidade_id == unit_id)
        if user_id:
            conds.append(Reservation.usuario_id == user_id)
        if not conds:
            return None

        stmt = (
            select(Reservation)
            .where(
                Reservation.area_comum_id == area_id,
                or_(*conds),
                Reservation.data_reserva < before_date,
                or_(
                    Reservation.status.in_(["CONFIRMADA", "CONCLUIDA"]),
                    Reservation.prioridade_queimada == True
                )
            )
            .order_by(Reservation.data_reserva.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def count_active_reservations_of_unit(self, area_id: int, unit_id: Optional[int], from_date: "date", user_id: Optional[int] = None) -> int:
        """Conta quantas reservas ativas/futuras a unidade ou usuário já possui nesta área comum."""
        from sqlalchemy import func, or_
        conds = []
        if unit_id:
            conds.append(Reservation.unidade_id == unit_id)
        if user_id:
            conds.append(Reservation.usuario_id == user_id)
        if not conds:
            return 0

        stmt = (
            select(func.count(Reservation.id))
            .where(
                Reservation.area_comum_id == area_id,
                or_(*conds),
                Reservation.data_reserva >= from_date,
                Reservation.status.in_(["CONFIRMADA", "BAIXA_PRIORIDADE", "OFERTA_RETOMADA"])
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def get_active_by_area_and_date(self, area_id: int, data_reserva: "date") -> List[Reservation]:
        """Retorna reservas vigentes (CONFIRMADA ou BAIXA_PRIORIDADE) para a área na data."""
        stmt = (
            select(Reservation)
            .options(
                selectinload(Reservation.usuario),
                selectinload(Reservation.unidade)
            )
            .where(
                Reservation.area_comum_id == area_id,
                Reservation.data_reserva == data_reserva,
                Reservation.status.in_(["CONFIRMADA", "BAIXA_PRIORIDADE"])
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def preempt_reservation(self, reservation_id: int, motivo: str = "Liberada para condômino prioritário") -> Optional[Reservation]:
        """Marca uma reserva de baixa prioridade como DESBANCADA."""
        res = await self.get_by_id(reservation_id)
        if not res:
            return None
        res.status = "DESBANCADA"
        res.observacoes = f"[{motivo}] {res.observacoes or ''}".strip()
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def promote_to_confirmed(self, reservation_id: int) -> Optional[Reservation]:
        """Efetiva em definitivo uma reserva que estava em baixa prioridade."""
        res = await self.get_by_id(reservation_id)
        if not res:
            return None
        res.status = "CONFIRMADA"
        await self.db.commit()
        await self.db.refresh(res)
        return res

    async def get_preempted_reservation_for_slot(self, area_id: int, data_reserva: "date") -> Optional[Reservation]:
        """Busca a última reserva que havia sido DESBANCADA para a mesma área e data."""
        stmt = (
            select(Reservation)
            .options(
                selectinload(Reservation.usuario),
                selectinload(Reservation.unidade),
                selectinload(Reservation.area_comum)
            )
            .where(
                Reservation.area_comum_id == area_id,
                Reservation.data_reserva == data_reserva,
                Reservation.status == "DESBANCADA"
            )
            .order_by(Reservation.atualizado_em.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_active_offers_for_user(self, usuario_id: int) -> List[Reservation]:
        """Retorna reservas que estão em OFERTA_RETOMADA e ainda não expiraram."""
        from datetime import datetime
        now = datetime.utcnow()
        stmt = (
            select(Reservation)
            .options(
                selectinload(Reservation.usuario),
                selectinload(Reservation.unidade),
                selectinload(Reservation.area_comum)
            )
            .where(
                Reservation.usuario_id == usuario_id,
                Reservation.status == "OFERTA_RETOMADA",
                Reservation.oferta_retomada_ate >= now
            )
            .order_by(Reservation.data_reserva.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def expire_stale_offers(self) -> int:
        """Expira automaticamente ofertas cujo prazo de resposta já passou."""
        from datetime import datetime
        now = datetime.utcnow()
        stmt = (
            select(Reservation)
            .where(
                Reservation.status == "OFERTA_RETOMADA",
                Reservation.oferta_retomada_ate < now
            )
        )
        result = await self.db.execute(stmt)
        stale = list(result.scalars().all())
        for r in stale:
            r.status = "CANCELADA"
            self.db.add(r)
        if stale:
            await self.db.commit()
        return len(stale)


