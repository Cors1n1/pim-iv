from datetime import date, datetime, time, timedelta
from typing import List, Optional
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reservation import CommonArea, Reservation
from app.models.user import User
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.reservation import (
    CommonAreaCreate,
    CommonAreaResponse,
    CommonAreaUpdate,
    ReservationCreate,
    ReservationPriorityCheckResponse,
    ReservationResponse
)
from app.services.email_service import EmailService


class ReservationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ReservationRepository(db)

    async def list_common_areas(self, include_inactive: bool = False) -> List[CommonAreaResponse]:
        """Retorna as áreas de lazer e convivência do condomínio."""
        areas = await self.repo.list_areas(include_inactive=include_inactive)
        return [CommonAreaResponse.model_validate(a) for a in areas]

    async def create_common_area(self, current_user: User, data: CommonAreaCreate) -> CommonAreaResponse:
        """Cadastra nova área comum (apenas síndico/admin)."""
        if current_user.tipo_usuario not in ("ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o síndico ou administradores podem cadastrar áreas comuns."
            )

        if data.hora_inicio >= data.hora_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O horário de abertura deve ser anterior ao horário de encerramento."
            )

        new_area = CommonArea(
            nome=data.nome.strip(),
            descricao=data.descricao.strip() if data.descricao else None,
            capacidade_pessoas=data.capacidade_pessoas,
            taxa_limpeza=data.taxa_limpeza,
            hora_inicio=data.hora_inicio,
            hora_fim=data.hora_fim,
            duracao_maxima_horas=data.duracao_maxima_horas,
            intervalo_dias_prioridade=data.intervalo_dias_prioridade,
            max_reservas_ativas=data.max_reservas_ativas,
            prazo_standby_horas=data.prazo_standby_horas,
            ativo=True
        )
        saved = await self.repo.create_area(new_area)
        return CommonAreaResponse.model_validate(saved)

    async def update_common_area(self, current_user: User, area_id: int, data: CommonAreaUpdate) -> CommonAreaResponse:
        """Atualiza regras operacionais e de governança justa de uma área comum (apenas síndico/admin)."""
        if current_user.tipo_usuario not in ("ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o síndico ou administradores podem alterar as regras das áreas comuns."
            )

        area = await self.repo.get_area_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área comum não encontrada."
            )

        new_inicio = data.hora_inicio if data.hora_inicio is not None else area.hora_inicio
        new_fim = data.hora_fim if data.hora_fim is not None else area.hora_fim

        if new_inicio >= new_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O horário de abertura deve ser anterior ao horário de encerramento."
            )

        if data.nome is not None:
            area.nome = data.nome.strip()
        if data.descricao is not None:
            area.descricao = data.descricao.strip() if data.descricao else None
        if data.capacidade_pessoas is not None:
            area.capacidade_pessoas = data.capacidade_pessoas
        if data.taxa_limpeza is not None:
            area.taxa_limpeza = data.taxa_limpeza
        if data.hora_inicio is not None:
            area.hora_inicio = data.hora_inicio
        if data.hora_fim is not None:
            area.hora_fim = data.hora_fim
        if data.duracao_maxima_horas is not None:
            area.duracao_maxima_horas = data.duracao_maxima_horas
        if data.intervalo_dias_prioridade is not None:
            area.intervalo_dias_prioridade = data.intervalo_dias_prioridade
        if data.max_reservas_ativas is not None:
            area.max_reservas_ativas = data.max_reservas_ativas
        if data.prazo_standby_horas is not None:
            area.prazo_standby_horas = data.prazo_standby_horas
        if data.ativo is not None:
            area.ativo = data.ativo

        updated = await self.repo.update_area(area)
        return CommonAreaResponse.model_validate(updated)

    async def check_priority(self, current_user: User, area_id: int, data_reserva: date) -> ReservationPriorityCheckResponse:
        """Verifica se a unidade do condômino possui Alta Prioridade ou Baixa Prioridade (Standby)."""
        area = await self.repo.get_area_by_id(area_id)
        if not area:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Área comum não encontrada.")

        settings = await SettingsRepository(self.db).get_settings()
        intervalo_req = area.intervalo_dias_prioridade or settings.intervalo_padrao_dias or 30
        max_ativas = area.max_reservas_ativas or 2

        # 1. Checa a data da última reserva confirmada ou com prioridade queimada
        last_res = await self.repo.get_last_reservation_of_unit(
            area_id=area_id,
            unit_id=current_user.unidade_id,
            before_date=data_reserva,
            user_id=current_user.id
        )
        dias_desde_ultima: Optional[int] = None
        motivo_queima = False

        if last_res:
            dias_desde_ultima = (data_reserva - last_res.data_reserva).days
            if getattr(last_res, "prioridade_queimada", False):
                intervalo_req = settings.dias_penalidade_queima or 30
                motivo_queima = True

        # 2. Checa quantas reservas futuras ativas o usuário/unidade possui
        reservas_ativas = await self.repo.count_active_reservations_of_unit(
            area_id=area_id,
            unit_id=current_user.unidade_id,
            from_date=date.today(),
            user_id=current_user.id
        )

        # Análise democrática e igualitária de prioridade (sem privilégio para síndico)
        if dias_desde_ultima is not None and dias_desde_ultima < intervalo_req:
            dias_restantes = intervalo_req - dias_desde_ultima
            msg_detalhe = (
                f"Sua prioridade foi queimada após cancelamento de vaga desbancada (penalidade: {intervalo_req} dias, restam {dias_restantes} dias)."
                if motivo_queima
                else f"Você ou sua unidade utilizou este espaço há {dias_desde_ultima} dias (carência regular: {intervalo_req} dias, restam {dias_restantes} dias)."
            )
            return ReservationPriorityCheckResponse(
                tem_prioridade_alta=False,
                status_proposto="BAIXA_PRIORIDADE",
                dias_desde_ultima=dias_desde_ultima,
                intervalo_requerido=intervalo_req,
                reservas_ativas=reservas_ativas,
                max_ativas=max_ativas,
                mensagem=(
                    f"{msg_detalhe} Sua reserva entrará em Standby (Baixa Prioridade). "
                    f"Caso nenhum condômino com prioridade regular solicite esta data até {area.prazo_standby_horas}h antes, ela será confirmada em definitivo!"
                )
            )

        if reservas_ativas >= max_ativas:
            return ReservationPriorityCheckResponse(
                tem_prioridade_alta=False,
                status_proposto="BAIXA_PRIORIDADE",
                dias_desde_ultima=dias_desde_ultima,
                intervalo_requerido=intervalo_req,
                reservas_ativas=reservas_ativas,
                max_ativas=max_ativas,
                mensagem=(
                    f"Você já possui {reservas_ativas} reserva(s) ativa(s) nesta área (limite prioritário: {max_ativas}). "
                    f"Esta nova solicitação será registrada em Standby (Baixa Prioridade)."
                )
            )

        return ReservationPriorityCheckResponse(
            tem_prioridade_alta=True,
            status_proposto="CONFIRMADA",
            dias_desde_ultima=dias_desde_ultima,
            intervalo_requerido=intervalo_req,
            reservas_ativas=reservas_ativas,
            max_ativas=max_ativas,
            mensagem="Você possui Prioridade Regular. Sua reserva será confirmada imediatamente."
        )

    async def list_reservations_for_user(self, current_user: User) -> List[ReservationResponse]:
        """
        Retorna as reservas com máscara de privacidade e LGPD, aplicando auto-promoção de standby
        quando a janela de corte (48h) for atingida sem contestação.
        """
        reservas = await self.repo.list_reservations()
        is_morador = current_user.tipo_usuario == "MORADOR"
        results: List[ReservationResponse] = []
        hoje = date.today()

        for r in reservas:
            # Auto-efetivação de reserva em Baixa Prioridade quando faltar menos de 48h
            if r.status == "BAIXA_PRIORIDADE":
                prazo_horas = r.area_comum.prazo_standby_horas if r.area_comum else 48
                dias_restantes = (r.data_reserva - hoje).days
                if dias_restantes * 24 < prazo_horas:
                    # Promove em definitivo
                    await self.repo.promote_to_confirmed(r.id)
                    r.status = "CONFIRMADA"

            is_mine = (r.usuario_id == current_user.id)
            area_nome = r.area_comum.nome if r.area_comum else "Área Comum"

            if is_morador and not is_mine:
                morador_nome = "Reservado por outro morador"
                unidade_desc = "Privado (LGPD)"
                obs = None
            else:
                morador_nome = r.usuario.nome if r.usuario else "Desconhecido"
                unidade_desc = f"{r.unidade.bloco} - Apto {r.unidade.numero}" if r.unidade else "Unidade não informada"
                obs = r.observacoes

            results.append(
                ReservationResponse(
                    id=r.id,
                    area_comum_id=r.area_comum_id,
                    area_nome=area_nome,
                    data_reserva=r.data_reserva,
                    hora_inicio=r.hora_inicio,
                    hora_fim=r.hora_fim,
                    status=r.status,
                    prioridade=r.prioridade or "ALTA",
                    prioridade_queimada=r.prioridade_queimada or False,
                    oferta_retomada_ate=r.oferta_retomada_ate,
                    total_convidados=len(r.guests) if getattr(r, "guests", None) else 0,
                    morador_nome=morador_nome,
                    unidade_desc=unidade_desc,
                    observacoes=obs,
                    is_mine=is_mine,
                    chave_entregue=r.chave_entregue,
                    chave_entregue_para=r.chave_entregue_para,
                    chave_entregue_em=r.chave_entregue_em,
                    chave_devolvida=r.chave_devolvida,
                    chave_devolvida_em=r.chave_devolvida_em,
                    criado_em=r.criado_em
                )
            )

        return results

    async def create_reservation(self, current_user: User, data: ReservationCreate) -> ReservationResponse:
        """Cria uma nova reserva aplicando a lógica de Governança Justa, Standby e Preempção."""
        if current_user.tipo_usuario == "PORTARIA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Porteiros não possuem permissão para realizar reservas. Reservas são exclusivas de moradores e síndicos."
            )

        if data.data_reserva < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível realizar reservas para datas no passado."
            )

        if data.hora_inicio >= data.hora_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O horário de início deve ser anterior ao horário de término."
            )

        area = await self.repo.get_area_by_id(data.area_comum_id)
        if not area or not area.ativo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área comum não encontrada ou desativada para uso."
            )

        # Validação 1: Funcionamento permitido da área
        if data.hora_inicio < area.hora_inicio or data.hora_fim > area.hora_fim:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Horário fora do funcionamento permitido para '{area.nome}'. "
                    f"Esta área funciona apenas entre {area.hora_inicio.strftime('%H:%M')} e {area.hora_fim.strftime('%H:%M')}."
                )
            )

        # Validação 2: Duração máxima contínua
        dummy_date = date(2000, 1, 1)
        dt_inicio = datetime.combine(dummy_date, data.hora_inicio)
        dt_fim = datetime.combine(dummy_date, data.hora_fim)
        duracao_segundos = (dt_fim - dt_inicio).total_seconds()
        duracao_horas = duracao_segundos / 3600.0

        if duracao_horas > area.duracao_maxima_horas:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Tempo de reserva excede o limite permitido para '{area.nome}'. "
                    f"O período máximo contínuo permitido pelo regulamento é de {area.duracao_maxima_horas} horas."
                )
            )

        # 3. Determina prioridade do solicitante
        p_check = await self.check_priority(current_user, data.area_comum_id, data.data_reserva)
        solicitante_alta_prioridade = p_check.tem_prioridade_alta

        # 4. Avalia reservas existentes na mesma data
        ativas_na_data = await self.repo.get_active_by_area_and_date(data.area_comum_id, data.data_reserva)
        reserva_confirmada = next((r for r in ativas_na_data if r.status == "CONFIRMADA"), None)
        reserva_standby = next((r for r in ativas_na_data if r.status == "BAIXA_PRIORIDADE"), None)

        dias_ate_evento = (data.data_reserva - date.today()).days
        horas_ate_evento = dias_ate_evento * 24

        if reserva_confirmada:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conflito de agendamento: esta área comum já possui reserva confirmada em definitivo para esta data."
            )

        if reserva_standby:
            # Se faltar menos de 48h, a reserva existente em standby já virou definitiva
            if horas_ate_evento < area.prazo_standby_horas:
                await self.repo.promote_to_confirmed(reserva_standby.id)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Esta data já foi confirmada em definitivo para outro condômino "
                        f"(janela de segurança de {area.prazo_standby_horas}h atingida)."
                    )
                )

            # Se ainda faltar mais de 48h:
            if solicitante_alta_prioridade:
                # Preempção Justa: Condômino prioritário assume a vaga!
                await self.repo.preempt_reservation(
                    reserva_standby.id,
                    motivo="Vaga cedida para condômino com prioridade regular (sem reservas recentes)"
                )
                novo_status = "CONFIRMADA"
                nova_prioridade = "ALTA"
            else:
                # O solicitante também é baixa prioridade. Não pode desbancar quem chegou primeiro
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Esta data já possui uma reserva em Standby (Baixa Prioridade). "
                        f"Como sua unidade também está em baixa prioridade, a preferência é de quem solicitou primeiro."
                    )
                )
        else:
            # Sem reservas concorrentes
            if solicitante_alta_prioridade:
                novo_status = "CONFIRMADA"
                nova_prioridade = "ALTA"
            else:
                novo_status = "BAIXA_PRIORIDADE"
                nova_prioridade = "BAIXA"

        new_res = Reservation(
            area_comum_id=data.area_comum_id,
            usuario_id=current_user.id,
            unidade_id=current_user.unidade_id,
            data_reserva=data.data_reserva,
            hora_inicio=data.hora_inicio,
            hora_fim=data.hora_fim,
            status=novo_status,
            prioridade=nova_prioridade,
            observacoes=data.observacoes.strip() if data.observacoes else None
        )

        try:
            created = await self.repo.create(new_res)
            reloaded = await self.repo.get_by_id(created.id)
            unidade_desc = f"{reloaded.unidade.bloco} - Apto {reloaded.unidade.numero}" if reloaded.unidade else "Minha unidade"
            return ReservationResponse(
                id=reloaded.id,
                area_comum_id=reloaded.area_comum_id,
                area_nome=reloaded.area_comum.nome if reloaded.area_comum else "Área Comum",
                data_reserva=reloaded.data_reserva,
                hora_inicio=reloaded.hora_inicio,
                hora_fim=reloaded.hora_fim,
                status=reloaded.status,
                prioridade=reloaded.prioridade or "ALTA",
                morador_nome=current_user.nome,
                unidade_desc=unidade_desc,
                observacoes=reloaded.observacoes,
                is_mine=True,
                chave_entregue=reloaded.chave_entregue,
                chave_entregue_para=reloaded.chave_entregue_para,
                chave_entregue_em=reloaded.chave_entregue_em,
                chave_devolvida=reloaded.chave_devolvida,
                chave_devolvida_em=reloaded.chave_devolvida_em,
                criado_em=reloaded.criado_em
            )
        except DBAPIError as err:
            await self.db.rollback()
            err_msg = str(err.orig) if hasattr(err, "orig") else str(err)
            if "CONFLITO_RESERVA" in err_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Conflito de agendamento: esta área comum já possui reserva confirmada para este horário nesta data."
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao processar reserva: {err_msg}"
            )

    async def cancel_reservation(self, current_user: User, reservation_id: int) -> ReservationResponse:
        """Cancela uma reserva existente com checagem de permissão."""
        res = await self.repo.get_by_id(reservation_id)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reserva não encontrada."
            )

        if current_user.tipo_usuario == "PORTARIA":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Porteiros não possuem permissão para cancelar reservas."
            )

        if current_user.tipo_usuario == "MORADOR" and res.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para cancelar a reserva de outro condômino."
            )

        if res.chave_entregue or res.chave_devolvida:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Esta reserva não pode ser cancelada porque a chave do espaço já foi retirada na portaria."
            )

        is_confirmed = (res.status == "CONFIRMADA")
        area_id = res.area_comum_id
        data_reserva = res.data_reserva

        cancelled = await self.repo.cancel(reservation_id)

        # Lógica Anti-Sabotagem e Oferta de Retomada
        if is_confirmed:
            desbancado = await self.repo.get_preempted_reservation_for_slot(area_id, data_reserva)
            if desbancado:
                settings = await SettingsRepository(self.db).get_settings()
                if settings.queima_prioridade_cancelamento:
                    cancelled.prioridade_queimada = True
                    await self.db.commit()

                prazo_h = settings.prazo_retomada_horas or 24
                desbancado.status = "OFERTA_RETOMADA"
                desbancado.oferta_retomada_ate = datetime.utcnow() + timedelta(hours=prazo_h)
                await self.db.commit()

                if settings.enviar_email_ativo and desbancado.usuario and desbancado.usuario.email:
                    anfitriao = desbancado.usuario.nome
                    area_nome = desbancado.area_comum.nome if desbancado.area_comum else "Área Comum"
                    data_formatada = desbancado.data_reserva.strftime("%d/%m/%Y")
                    expira_formatada = (datetime.utcnow() + timedelta(hours=prazo_h)).strftime("%d/%m/%Y às %H:%M")

                    async def _send_offer():
                        await EmailService.send_slot_recovery_offer(
                            to_email=desbancado.usuario.email,
                            resident_name=anfitriao,
                            area_name=area_nome,
                            date_str=data_formatada,
                            expires_str=expira_formatada,
                            condo_name=settings.nome_condominio
                        )

                    asyncio.create_task(_send_offer())

        unidade_desc = f"{cancelled.unidade.bloco} - Apto {cancelled.unidade.numero}" if cancelled.unidade else "Unidade"
        return ReservationResponse(
            id=cancelled.id,
            area_comum_id=cancelled.area_comum_id,
            area_nome=cancelled.area_comum.nome if cancelled.area_comum else "Área Comum",
            data_reserva=cancelled.data_reserva,
            hora_inicio=cancelled.hora_inicio,
            hora_fim=cancelled.hora_fim,
            status=cancelled.status,
            prioridade=cancelled.prioridade or "ALTA",
            prioridade_queimada=cancelled.prioridade_queimada or False,
            oferta_retomada_ate=cancelled.oferta_retomada_ate,
            total_convidados=len(cancelled.guests) if getattr(cancelled, "guests", None) else 0,
            morador_nome=cancelled.usuario.nome if cancelled.usuario else "Morador",
            unidade_desc=unidade_desc,
            observacoes=cancelled.observacoes,
            is_mine=(cancelled.usuario_id == current_user.id),
            chave_entregue=cancelled.chave_entregue,
            chave_entregue_para=cancelled.chave_entregue_para,
            chave_entregue_em=cancelled.chave_entregue_em,
            chave_devolvida=cancelled.chave_devolvida,
            chave_devolvida_em=cancelled.chave_devolvida_em,
            criado_em=cancelled.criado_em
        )

    async def list_active_offers(self, current_user: User) -> List[ReservationResponse]:
        """Retorna ofertas de retomada de vaga vigentes para o condômino."""
        await self.repo.expire_stale_offers()
        offers = await self.repo.get_active_offers_for_user(current_user.id)
        res_list = []
        for r in offers:
            u_desc = f"{r.unidade.bloco} - Apto {r.unidade.numero}" if r.unidade else "Unidade"
            res_list.append(ReservationResponse(
                id=r.id,
                area_comum_id=r.area_comum_id,
                area_nome=r.area_comum.nome if r.area_comum else "Área Comum",
                data_reserva=r.data_reserva,
                hora_inicio=r.hora_inicio,
                hora_fim=r.hora_fim,
                status=r.status,
                prioridade=r.prioridade or "ALTA",
                prioridade_queimada=r.prioridade_queimada or False,
                oferta_retomada_ate=r.oferta_retomada_ate,
                total_convidados=len(r.guests) if getattr(r, "guests", None) else 0,
                morador_nome=r.usuario.nome if r.usuario else "Morador",
                unidade_desc=u_desc,
                observacoes=r.observacoes,
                is_mine=True,
                chave_entregue=r.chave_entregue,
                chave_entregue_para=r.chave_entregue_para,
                chave_entregue_em=r.chave_entregue_em,
                chave_devolvida=r.chave_devolvida,
                chave_devolvida_em=r.chave_devolvida_em,
                criado_em=r.criado_em
            ))
        return res_list

    async def accept_offer(self, current_user: User, reservation_id: int) -> ReservationResponse:
        """Morador aceita a oferta de retomada da vaga com direito de preferência."""
        res = await self.repo.get_by_id(reservation_id)
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        if res.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado a esta oferta.")

        if res.status != "OFERTA_RETOMADA":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Esta reserva não possui uma oferta de retomada pendente.")

        if res.oferta_retomada_ate and res.oferta_retomada_ate < datetime.utcnow():
            res.status = "CANCELADA"
            await self.db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O prazo para aceitar esta vaga expirou.")

        res.status = "CONFIRMADA"
        res.prioridade = "ALTA"
        res.oferta_retomada_ate = None
        await self.db.commit()
        await self.db.refresh(res)

        u_desc = f"{res.unidade.bloco} - Apto {res.unidade.numero}" if res.unidade else "Unidade"
        return ReservationResponse(
            id=res.id,
            area_comum_id=res.area_comum_id,
            area_nome=res.area_comum.nome if res.area_comum else "Área Comum",
            data_reserva=res.data_reserva,
            hora_inicio=res.hora_inicio,
            hora_fim=res.hora_fim,
            status=res.status,
            prioridade=res.prioridade,
            prioridade_queimada=res.prioridade_queimada or False,
            oferta_retomada_ate=None,
            total_convidados=len(res.guests) if getattr(res, "guests", None) else 0,
            morador_nome=res.usuario.nome if res.usuario else "Morador",
            unidade_desc=u_desc,
            observacoes=res.observacoes,
            is_mine=True,
            chave_entregue=res.chave_entregue,
            chave_entregue_para=res.chave_entregue_para,
            chave_entregue_em=res.chave_entregue_em,
            chave_devolvida=res.chave_devolvida,
            chave_devolvida_em=res.chave_devolvida_em,
            criado_em=res.criado_em
        )

    async def decline_offer(self, current_user: User, reservation_id: int) -> ReservationResponse:
        """Morador declina a oferta e libera a data para o condomínio."""
        res = await self.repo.get_by_id(reservation_id)
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        if res.usuario_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso não autorizado a esta oferta.")

        res.status = "CANCELADA"
        res.oferta_retomada_ate = None
        await self.db.commit()
        await self.db.refresh(res)

        u_desc = f"{res.unidade.bloco} - Apto {res.unidade.numero}" if res.unidade else "Unidade"
        return ReservationResponse(
            id=res.id,
            area_comum_id=res.area_comum_id,
            area_nome=res.area_comum.nome if res.area_comum else "Área Comum",
            data_reserva=res.data_reserva,
            hora_inicio=res.hora_inicio,
            hora_fim=res.hora_fim,
            status=res.status,
            prioridade=res.prioridade or "ALTA",
            prioridade_queimada=res.prioridade_queimada or False,
            oferta_retomada_ate=None,
            total_convidados=len(res.guests) if getattr(res, "guests", None) else 0,
            morador_nome=res.usuario.nome if res.usuario else "Morador",
            unidade_desc=u_desc,
            observacoes=res.observacoes,
            is_mine=True,
            chave_entregue=res.chave_entregue,
            chave_entregue_para=res.chave_entregue_para,
            chave_entregue_em=res.chave_entregue_em,
            chave_devolvida=res.chave_devolvida,
            chave_devolvida_em=res.chave_devolvida_em,
            criado_em=res.criado_em
        )

    async def handover_key(self, current_user: User, reservation_id: int, entregue_para: str) -> ReservationResponse:
        """Registra a entrega da chave pelo porteiro ou síndico."""
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas funcionários da portaria ou administração podem registrar a entrega de chaves."
            )

        res = await self.repo.get_by_id(reservation_id)
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        if res.status != "CONFIRMADA":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível entregar chave de reserva em standby ou cancelada."
            )

        if res.chave_entregue:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A chave deste espaço já foi entregue.")

        updated = await self.repo.handover_key(reservation_id, current_user.id, entregue_para.strip())
        unidade_desc = f"{updated.unidade.bloco} - Apto {updated.unidade.numero}" if updated.unidade else "Unidade"
        return ReservationResponse(
            id=updated.id,
            area_comum_id=updated.area_comum_id,
            area_nome=updated.area_comum.nome if updated.area_comum else "Área Comum",
            data_reserva=updated.data_reserva,
            hora_inicio=updated.hora_inicio,
            hora_fim=updated.hora_fim,
            status=updated.status,
            prioridade=updated.prioridade or "ALTA",
            morador_nome=updated.usuario.nome if updated.usuario else "Morador",
            unidade_desc=unidade_desc,
            observacoes=updated.observacoes,
            is_mine=(updated.usuario_id == current_user.id),
            chave_entregue=updated.chave_entregue,
            chave_entregue_para=updated.chave_entregue_para,
            chave_entregue_em=updated.chave_entregue_em,
            chave_devolvida=updated.chave_devolvida,
            chave_devolvida_em=updated.chave_devolvida_em,
            criado_em=updated.criado_em
        )

    async def return_key(self, current_user: User, reservation_id: int) -> ReservationResponse:
        """Registra a devolução da chave na portaria."""
        if current_user.tipo_usuario not in ("PORTARIA", "ADMIN", "SINDICO"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas funcionários da portaria ou administração podem registrar a devolução de chaves."
            )

        res = await self.repo.get_by_id(reservation_id)
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada.")

        if not res.chave_entregue:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A chave ainda não foi registrada como entregue.")

        if res.chave_devolvida:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A chave já foi registrada como devolvida.")

        updated = await self.repo.return_key(reservation_id)
        unidade_desc = f"{updated.unidade.bloco} - Apto {updated.unidade.numero}" if updated.unidade else "Unidade"
        return ReservationResponse(
            id=updated.id,
            area_comum_id=updated.area_comum_id,
            area_nome=updated.area_comum.nome if updated.area_comum else "Área Comum",
            data_reserva=updated.data_reserva,
            hora_inicio=updated.hora_inicio,
            hora_fim=updated.hora_fim,
            status=updated.status,
            prioridade=updated.prioridade or "ALTA",
            morador_nome=updated.usuario.nome if updated.usuario else "Morador",
            unidade_desc=unidade_desc,
            observacoes=updated.observacoes,
            is_mine=(updated.usuario_id == current_user.id),
            chave_entregue=updated.chave_entregue,
            chave_entregue_para=updated.chave_entregue_para,
            chave_entregue_em=updated.chave_entregue_em,
            chave_devolvida=updated.chave_devolvida,
            chave_devolvida_em=updated.chave_devolvida_em,
            criado_em=updated.criado_em
        )
