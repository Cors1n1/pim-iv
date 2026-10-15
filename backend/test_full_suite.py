import asyncio
import os
import sys
from datetime import date, time, timedelta

# Configura path para a pasta backend
sys.path.insert(0, r"c:\Users\Corsini\Desktop\projetos\PIM_IV\backend")

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.reservation import Reservation
from app.models.guest import ReservationGuest
from app.models.settings import CondoSettings
from app.services.settings_service import SettingsService
from app.services.guest_service import GuestService
from app.schemas.guest import GuestCreate
from app.schemas.settings import CondoSettingsUpdate
from fastapi import HTTPException
from sqlalchemy import select

async def run_tests():
    print("=== INICIANDO SUITE DE TESTES DAS REGRAS REFINADAS ===")
    async with AsyncSessionLocal() as db:
        # 1. Carrega ou cria usuário morador e síndico
        result_morador = await db.execute(select(User).where(User.email == "morador@condominio.com"))
        morador = result_morador.scalar_one_or_none()
        
        result_sindico = await db.execute(select(User).where(User.email == "admin@condominio.com"))
        sindico = result_sindico.scalar_one_or_none()

        assert morador is not None, "Morador não encontrado no banco!"
        assert sindico is not None, "Síndico não encontrado no banco!"

        # 2. Testa SettingsService com dias_penalidade_queima
        print("[TESTE 1] Atualização modular de dias_penalidade_queima nas configurações...")
        settings_service = SettingsService(db)
        updated_settings = await settings_service.update_settings(
            current_user=sindico,
            data=CondoSettingsUpdate(dias_penalidade_queima=45, queima_prioridade_cancelamento=True)
        )
        assert updated_settings.dias_penalidade_queima == 45, f"Esperava 45, obteve {updated_settings.dias_penalidade_queima}"
        print("  -> OK! dias_penalidade_queima atualizado para 45 dias.")

        # 3. Busca ou cria reserva para o morador para testar a governança de convidados
        print("[TESTE 2] Localizando reserva do morador para validar fluxo de convidados...")
        hoje = date.today()
        result_res = await db.execute(
            select(Reservation).where(
                Reservation.usuario_id == morador.id,
                Reservation.data_reserva == hoje,
                Reservation.status == "CONFIRMADA"
            )
        )
        nova_reserva = result_res.scalars().first()
        if not nova_reserva:
            nova_reserva = Reservation(
                usuario_id=morador.id,
                unidade_id=morador.unidade_id,
                area_comum_id=1,
                data_reserva=hoje,
                hora_inicio=time(12, 0),
                hora_fim=time(18, 0),
                status="CONFIRMADA",
                observacoes="Festa de Aniversário Particular"
            )
            db.add(nova_reserva)
            await db.commit()
            await db.refresh(nova_reserva)
        print(f"  -> Usando Reserva ID {nova_reserva.id}")

        guest_service = GuestService(db)

        # 4. Morador adiciona convidado SEM documento (opcional)
        print("[TESTE 3] Morador cadastra convidado SEM CPF/RG (documento nulo)...")
        guest_payload = GuestCreate(
            nome_completo="Amigo Teste Sem Documento",
            documento=None,
            email=None,
            enviar_convite=False
        )
        guest = await guest_service.add_guest(
            current_user=morador,
            reservation_id=nova_reserva.id,
            data=guest_payload
        )
        assert guest.nome_completo == "Amigo Teste Sem Documento"
        assert guest.documento is None
        print(f"  -> OK! Convidado {guest.id} cadastrado com sucesso sem documento obrigatório.")

        # 5. Tentativa do Síndico de ADICIONAR convidado na festa do Morador (deve ser 403 Forbidden)
        print("[TESTE 4] Tentativa do síndico de adicionar convidado na festa do vizinho...")
        try:
            await guest_service.add_guest(
                current_user=sindico,
                reservation_id=nova_reserva.id,
                data=GuestCreate(nome_completo="Intruso do Síndico")
            )
            assert False, "ERRO: O síndico conseguiu adicionar convidado na festa de um morador!"
        except HTTPException as e:
            assert e.status_code == 403, f"Esperava 403, obteve {e.status_code}"
            print(f"  -> OK! Bloqueado com 403 Forbidden conforme LGPD e privacidade: {e.detail}")

        # 6. Tentativa do Síndico de DELETAR convidado do Morador (deve ser 403 Forbidden)
        print("[TESTE 5] Tentativa do síndico de excluir convidado do vizinho...")
        try:
            await guest_service.delete_guest(
                current_user=sindico,
                reservation_id=nova_reserva.id,
                guest_id=guest.id
            )
            assert False, "ERRO: O síndico conseguiu excluir convidado da festa de um morador!"
        except HTTPException as e:
            assert e.status_code == 403, f"Esperava 403, obteve {e.status_code}"
            print(f"  -> OK! Bloqueado com 403 Forbidden: {e.detail}")

        # 7. Portaria listando convidados de hoje (GET /api/guests/today)
        print("[TESTE 6] Portaria listando convidados esperados para hoje...")
        portaria_user = User(id=999, tipo_usuario="PORTARIA", nome="Porteiro de Plantão")
        today_guests = await guest_service.list_today_guests(current_user=portaria_user)
        assert len(today_guests) >= 1
        found_guest = next((g for g in today_guests if g["id"] == guest.id), None)
        assert found_guest is not None
        print(f"  -> OK! Convidado encontrado na guarita: {found_guest['nome_completo']} com destino à área {found_guest['area_nome']}")

        # 8. Portaria registrando entrada e depois saída
        print("[TESTE 7] Portaria registrando ENTRADA do convidado...")
        g_in = await guest_service.checkin_guest(current_user=portaria_user, reservation_id=nova_reserva.id, guest_id=guest.id)
        assert g_in.entrada_registrada is True
        assert g_in.entrada_em is not None
        print(f"  -> OK! Entrada registrada às {g_in.entrada_em}")

        print("[TESTE 8] Portaria registrando SAÍDA do convidado...")
        g_out = await guest_service.checkout_guest(current_user=portaria_user, guest_id=guest.id)
        assert g_out.saida_registrada is True
        assert g_out.saida_em is not None
        print(f"  -> OK! Saída registrada às {g_out.saida_em}")

        # 9. Morador excluindo seu próprio convidado
        print("[TESTE 9] Morador titular excluindo o convidado...")
        deleted = await guest_service.delete_guest(
            current_user=morador,
            reservation_id=nova_reserva.id,
            guest_id=guest.id
        )
        assert deleted is not None
        print("  -> OK! Morador titular excluiu seu convidado com sucesso.")

        # Restaura configuração para 30 dias
        await settings_service.update_settings(current_user=sindico, data=CondoSettingsUpdate(dias_penalidade_queima=30))
        await db.commit()
        print("=== TODOS OS 9 TESTES PASSARAM COM 100% DE SUCESSO! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
