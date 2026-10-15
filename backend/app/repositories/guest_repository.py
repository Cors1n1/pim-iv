from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guest import ReservationGuest


class GuestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_reservation(self, reserva_id: int) -> List[ReservationGuest]:
        stmt = select(ReservationGuest).filter(
            ReservationGuest.reserva_id == reserva_id
        ).order_by(ReservationGuest.nome_completo.asc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, guest_id: int) -> Optional[ReservationGuest]:
        stmt = select(ReservationGuest).filter(ReservationGuest.id == guest_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, guest: ReservationGuest) -> ReservationGuest:
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def update(self, guest: ReservationGuest) -> ReservationGuest:
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def delete(self, guest: ReservationGuest) -> None:
        await self.db.delete(guest)
        await self.db.commit()

    async def register_entry(self, guest: ReservationGuest) -> ReservationGuest:
        guest.entrada_registrada = True
        guest.entrada_em = datetime.utcnow()
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def register_exit(self, guest: ReservationGuest) -> ReservationGuest:
        guest.saida_registrada = True
        guest.saida_em = datetime.utcnow()
        self.db.add(guest)
        await self.db.commit()
        await self.db.refresh(guest)
        return guest

    async def list_today_guests(self) -> List[dict]:
        from datetime import date
        from app.models.reservation import Reservation, CommonArea
        from app.models.user import User, Unit

        today = date.today()
        stmt = (
            select(ReservationGuest, Reservation, CommonArea, Unit, User)
            .join(Reservation, ReservationGuest.reserva_id == Reservation.id)
            .join(CommonArea, Reservation.area_comum_id == CommonArea.id)
            .outerjoin(Unit, Reservation.unidade_id == Unit.id)
            .outerjoin(User, Reservation.usuario_id == User.id)
            .filter(Reservation.data_reserva == today, Reservation.status.in_(["CONFIRMADA", "BAIXA_PRIORIDADE"]))
            .order_by(ReservationGuest.nome_completo.asc())
        )
        result = await self.db.execute(stmt)
        items = []
        for g, res, area, unit, host in result.all():
            items.append({
                "id": g.id,
                "reserva_id": res.id,
                "nome_completo": g.nome_completo,
                "documento": g.documento,
                "email": g.email,
                "convite_enviado": g.convite_enviado,
                "entrada_registrada": g.entrada_registrada,
                "entrada_em": g.entrada_em,
                "saida_registrada": g.saida_registrada,
                "saida_em": g.saida_em,
                "area_nome": area.nome,
                "anfitriao_nome": host.nome if host else "Morador",
                "unidade_desc": f"{unit.bloco} - Apto {unit.numero}" if unit else "Condômino",
                "hora_inicio": res.hora_inicio.strftime("%H:%M") if res.hora_inicio else "--:--",
                "hora_fim": res.hora_fim.strftime("%H:%M") if res.hora_fim else "--:--"
            })
        return items
