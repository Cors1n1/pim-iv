import asyncio
from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.guest import ReservationGuest
from app.models.user import User
from app.repositories.guest_repository import GuestRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.guest import GuestCreate, GuestResponse
from app.services.email_service import EmailService


class GuestService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.guest_repo = GuestRepository(db)
        self.res_repo = ReservationRepository(db)
        self.settings_repo = SettingsRepository(db)

    async def list_guests(self, current_user: User, reservation_id: int) -> List[GuestResponse]:
        reserva = await self.res_repo.get_by_id(reservation_id)
        if not reserva:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        is_owner = (reserva.usuario_id == current_user.id)
        is_staff = current_user.tipo_usuario in ("ADMIN", "SINDICO", "PORTARIA")
        if not is_owner and not is_staff:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito ao titular da reserva ou portaria.")

        guests = await self.guest_repo.list_by_reservation(reservation_id)
        return [GuestResponse.model_validate(g) for g in guests]

    async def add_guest(
        self,
        current_user: User,
        reservation_id: int,
        data: GuestCreate,
        background_tasks: Optional[BackgroundTasks] = None,
        **kwargs
    ) -> GuestResponse:
        reserva = await self.res_repo.get_by_id(reservation_id)
        if not reserva:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        # PRIVACIDADE ABSOLUTA: Apenas o condômino titular pode gerenciar convidados de sua reserva
        is_owner = (reserva.usuario_id == current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o condômino titular da reserva pode gerenciar seus convidados."
            )

        if reserva.status in ("CANCELADA", "DESBANCADA"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não é possível adicionar convidados para reservas inativas.")

        # Limite de convidados baseado na capacidade da área
        current_guests = await self.guest_repo.list_by_reservation(reservation_id)
        if reserva.area_comum and len(current_guests) >= reserva.area_comum.capacidade_pessoas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limite de capacidade atingido ({reserva.area_comum.capacidade_pessoas} pessoas)."
            )

        doc_clean = data.documento.strip() if data.documento and data.documento.strip() else None
        email_clean = data.email.strip() if data.email and data.email.strip() else None

        guest = ReservationGuest(
            reserva_id=reservation_id,
            nome_completo=data.nome_completo.strip(),
            documento=doc_clean,
            email=email_clean,
            convite_enviado=False
        )

        saved = await self.guest_repo.create(guest)

        # Dispara convite por e-mail se solicitado explicitamente pelo morador
        if data.enviar_convite and email_clean:
            settings = await self.settings_repo.get_settings()
            if settings.enviar_email_ativo:
                anfitriao = reserva.usuario.nome if reserva.usuario else "Condômino"
                unidade_desc = f"{reserva.unidade.bloco} - Apto {reserva.unidade.numero}" if reserva.unidade else "Residência"
                area_nome = reserva.area_comum.nome if reserva.area_comum else "Espaço Comum"
                data_formatada = reserva.data_reserva.strftime("%d/%m/%Y")
                h_ini = reserva.hora_inicio.strftime("%H:%M") if reserva.hora_inicio else "08:00"
                h_fim = reserva.hora_fim.strftime("%H:%M") if reserva.hora_fim else "22:00"

                # Marca convite como enviado para que a interface receba confirmação instantânea (zero freeze)
                saved.convite_enviado = True
                await self.guest_repo.update(saved)

                # Despacha o disparo de e-mail de forma assíncrona desacoplada
                asyncio.create_task(
                    EmailService.send_guest_invitation(
                        to_email=email_clean,
                        guest_name=saved.nome_completo,
                        host_name=anfitriao,
                        unit_desc=unidade_desc,
                        area_name=area_nome,
                        date_str=data_formatada,
                        time_start=h_ini,
                        time_end=h_fim,
                        condo_name=settings.nome_condominio,
                        condo_address=settings.endereco
                    )
                )

        return GuestResponse.model_validate(saved)

    async def delete_guest(self, current_user: User, reservation_id: int, guest_id: int) -> dict:
        reserva = await self.res_repo.get_by_id(reservation_id)
        if not reserva:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        is_owner = (reserva.usuario_id == current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o condômino titular da reserva pode gerenciar seus convidados."
            )

        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest or guest.reserva_id != reservation_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado nesta reserva.")

        await self.guest_repo.delete(guest)
        return {"message": "Convidado removido com sucesso."}

    async def checkin_guest(self, current_user: User, reservation_id: int, guest_id: int) -> GuestResponse:
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Exclusivo para a portaria ou administração.")

        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest or guest.reserva_id != reservation_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado nesta reserva.")

        updated = await self.guest_repo.register_entry(guest)
        return GuestResponse.model_validate(updated)

    async def checkout_guest(self, current_user: User, guest_id: int) -> GuestResponse:
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Exclusivo para a portaria ou administração.")

        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado.")

        updated = await self.guest_repo.register_exit(guest)
        return GuestResponse.model_validate(updated)

    async def list_today_guests(self, current_user: User) -> List[dict]:
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Exclusivo para a portaria ou administração.")
        return await self.guest_repo.list_today_guests()

    async def resend_invite(
        self,
        current_user: User,
        guest_id: int,
        background_tasks: Optional[BackgroundTasks] = None,
        **kwargs
    ) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Convidado não encontrado.")
        reserva = await self.res_repo.get_by_id(guest.reserva_id)
        if not reserva:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        is_owner = (reserva.usuario_id == current_user.id)
        if not is_owner:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Apenas o titular da reserva pode reenviar convites.")

        if not guest.email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Convidado não possui e-mail cadastrado.")

        settings = await self.settings_repo.get_settings()
        if settings.enviar_email_ativo:
            anfitriao = reserva.usuario.nome if reserva.usuario else "Condômino"
            unidade_desc = f"{reserva.unidade.bloco} - Apto {reserva.unidade.numero}" if reserva.unidade else "Residência"
            area_nome = reserva.area_comum.nome if reserva.area_comum else "Espaço Comum"
            data_formatada = reserva.data_reserva.strftime("%d/%m/%Y")
            h_ini = reserva.hora_inicio.strftime("%H:%M") if reserva.hora_inicio else "08:00"
            h_fim = reserva.hora_fim.strftime("%H:%M") if reserva.hora_fim else "22:00"

            guest.convite_enviado = True
            await self.guest_repo.update(guest)

            asyncio.create_task(
                EmailService.send_guest_invitation(
                    to_email=guest.email.strip(),
                    guest_name=guest.nome_completo,
                    host_name=anfitriao,
                    unit_desc=unidade_desc,
                    area_name=area_nome,
                    date_str=data_formatada,
                    time_start=h_ini,
                    time_end=h_fim,
                    condo_name=settings.nome_condominio,
                    condo_address=settings.endereco
                )
            )

        return GuestResponse.model_validate(guest)
