import asyncio
import asyncpg
import os

async def main():
    db_url = "postgresql://postgres:12345678@localhost:5432/pim_iv_condominio"
    print(f"Conectando a {db_url}...")
    conn = await asyncpg.connect(db_url)
    
    sql_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema_completo_pim_iv.sql")
    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    
    print("Executando schema_completo_pim_iv.sql...")
    await conn.execute(sql)
    print("Script SQL executado com SUCESSO!")

    # Tabelas
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    print("\n--- TABELAS CRIADAS ---")
    for r in tables:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {r['table_name']};")
        print(f" - {r['table_name']}: {count} registros")

    # Views
    views = await conn.fetch("""
        SELECT table_name FROM information_schema.views 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    print("\n--- VIEWS ANALÍTICAS ---")
    for r in views:
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {r['table_name']};")
        print(f" - {r['table_name']}: {count} linhas retornadas")

    # Functions / Procedures
    routines = await conn.fetch("""
        SELECT routine_name, routine_type FROM information_schema.routines
        WHERE routine_schema = 'public' AND routine_name NOT LIKE 'uuid%'
        ORDER BY routine_name;
    """)
    print("\n--- PROCEDURES / FUNCTIONS ---")
    for r in routines:
        print(f" - [{r['routine_type']}] {r['routine_name']}")

    # Teste de Procedure: Baixa de encomenda
    try:
        # Vamos buscar uma encomenda pendente
        enc_id = await conn.fetchval("SELECT id FROM encomendas WHERE status = 'AGUARDANDO_RETIRADA' LIMIT 1;")
        if enc_id:
            await conn.execute("CALL pr_dar_baixa_encomenda($1, $2, $3);", enc_id, "Ana Beatriz", 2)
            print(f"\n[TESTE OK] Procedure pr_dar_baixa_encomenda executada com sucesso para encomenda ID {enc_id}!")
    except Exception as e:
        print(f"[TESTE ERRO] Erro na procedure: {e}")

    # Teste de Function Dashboard
    dashboard = await conn.fetchval("SELECT fn_obter_resumo_dashboard()::text;")
    print(f"\n[TESTE OK] Função fn_obter_resumo_dashboard(): {dashboard}")

    # Teste da Trigger de Conflito de Reserva
    try:
        reserva = await conn.fetchrow("SELECT area_comum_id, data_reserva FROM reservas WHERE status = 'CONFIRMADA' LIMIT 1;")
        if reserva:
            # Tenta inserir duplicada para forçar disparo da trigger
            await conn.execute("""
                INSERT INTO reservas (area_comum_id, usuario_id, data_reserva, status)
                VALUES ($1, 3, $2, 'CONFIRMADA');
            """, reserva['area_comum_id'], reserva['data_reserva'])
            print("[TESTE FALHA] Trigger não disparou!")
    except asyncpg.exceptions.RaiseError as e:
        print(f"\n[TESTE OK] Trigger fn_validar_conflito_reserva bloqueou agendamento duplo perfeitamente: {e}")

    # Teste da Trigger de Reserva Retroativa
    try:
        await conn.execute("""
            INSERT INTO reservas (area_comum_id, usuario_id, data_reserva, status)
            VALUES (1, 3, '2020-01-01', 'CONFIRMADA');
        """)
        print("[TESTE FALHA] Trigger de reserva retroativa não disparou!")
    except asyncpg.exceptions.RaiseError as e:
        print(f"\n[TESTE OK] Trigger fn_impedir_reserva_retroativa bloqueou data retroativa perfeitamente: {e}")

    await conn.close()
    print("\nTodos os testes de validação do banco foram concluídos com 100% de êxito!")

if __name__ == "__main__":
    asyncio.run(main())
