import asyncio
import httpx
from datetime import date, timedelta

BASE_URL = "http://127.0.0.1:8000"

async def test_full_flow():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("=== 1. TESTE PUBLIC SETTINGS ===")
        r = await client.get("/api/settings/public")
        assert r.status_code == 200, f"Public settings failed: {r.text}"
        data = r.json()
        print(f"OK: Nome: {data['nome_condominio']}")

        print("\n=== 2. LOGIN DO SÍNDICO ===")
        r = await client.post("/api/auth/login", json={"email": "admin@condominio.com", "senha": "Admin@123"})
        assert r.status_code == 200, f"Login failed: {r.text}"
        admin_token = r.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        print("\n=== 3. ATUALIZAR CONFIGURAÇÕES VIA SÍNDICO ===")
        r = await client.put(
            "/api/settings",
            headers=admin_headers,
            json={
                "nome_condominio": "Residencial Bela Vista Premium",
                "prazo_retomada_horas": 24,
                "prazo_standby_horas": 48,
                "intervalo_padrao_dias": 30,
                "queima_prioridade_cancelamento": True,
                "enviar_email_ativo": True
            }
        )
        assert r.status_code == 200, f"Update settings failed: {r.text}"
        print(f"OK: Atualizado para: {r.json()['nome_condominio']}")

        print("\n=== 4. VERIFICAR QUE PUBLIC REFLETE ATUALIZAÇÃO ===")
        r = await client.get("/api/settings/public")
        assert r.json()["nome_condominio"] == "Residencial Bela Vista Premium"
        print("OK: Public endpoint reflete novo nome imediatamente!")

        print("\n=== 5. LOGIN DE DOIS MORADORES ===")
        r = await client.post("/api/auth/login", json={"email": "morador@condominio.com", "senha": "Morador@123"})
        m1_token = r.json()["access_token"]
        m1_headers = {"Authorization": f"Bearer {m1_token}"}

        r = await client.post("/api/auth/login", json={"email": "victorcorsini@gmail.com", "senha": "Morador@123"})
        m2_token = r.json()["access_token"]
        m2_headers = {"Authorization": f"Bearer {m2_token}"}

        print("\n=== 6. SELECIONAR UMA ÁREA COMUM ===")
        r = await client.get("/api/reservations/areas", headers=m1_headers)
        areas = r.json()
        area_id = areas[0]["id"]
        print(f"OK: Área selecionada ID {area_id} ({areas[0]['nome']})")

        target_date = (date.today() + timedelta(days=20)).isoformat()

        print("\n=== 7. MORADOR 1 CRIA RESERVA ===")
        r = await client.post(
            "/api/reservations",
            headers=m1_headers,
            json={
                "area_comum_id": area_id,
                "data_reserva": target_date,
                "hora_inicio": "12:00:00",
                "hora_fim": "16:00:00",
                "observacoes": "Teste de Reserva Justa M1"
            }
        )
        res1 = r.json()
        res1_id = res1["id"]
        print(f"OK: Reserva 1 criada status = {res1['status']} (ID: {res1_id})")

        print("\n=== 8. TESTE DO MÓDULO DE CONVIDADOS NA RESERVA 1 ===")
        r = await client.post(
            f"/api/guests/reservation/{res1_id}",
            headers=m1_headers,
            json={
                "nome_completo": "Carlos Eduardo Pereira",
                "documento": "44.555.666-7",
                "email": "carlos.teste@email.com",
                "enviar_convite": True
            }
        )
        assert r.status_code == 201, f"Create guest failed: {r.text}"
        guest_id = r.json()["id"]
        print(f"OK: Convidado criado com ID {guest_id} (convite enviado: {r.json()['convite_enviado']})")

        r = await client.get(f"/api/guests/reservation/{res1_id}", headers=m1_headers)
        guests = r.json()
        assert len(guests) >= 1
        print(f"OK: Listagem de convidados retornou {len(guests)} pessoas")

        print("\n=== 9. PORTARIA REALIZA CHECK-IN DO CONVIDADO ===")
        r = await client.post("/api/auth/login", json={"email": "portaria@condominio.com", "senha": "Portaria@123"})
        portaria_token = r.json()["access_token"]
        portaria_headers = {"Authorization": f"Bearer {portaria_token}"}

        r = await client.put(f"/api/guests/{guest_id}/checkin", headers=portaria_headers)
        assert r.status_code == 200
        assert r.json()["entrada_registrada"] is True
        print(f"OK: Check-in realizado com sucesso às {r.json()['entrada_em']}")

        print("\n=== 10. LIMPAR DADOS DO TESTE E RESTAURAR NOME PADRÃO ===")
        await client.put(
            "/api/settings",
            headers=admin_headers,
            json={"nome_condominio": "Residencial Bela Vista"}
        )
        await client.put(f"/api/reservations/{res1_id}/cancel", headers=m1_headers)
        print("OK: Reserva de teste cancelada e nome restaurado.")

        print("\n>>> TODOS OS TESTES PASSARAM COM 100% DE SUCESSO! <<<")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
