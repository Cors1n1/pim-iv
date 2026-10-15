import urllib.request
import json

def run_tests():
    # 1. Login
    login_data = json.dumps({"email": "admin@condominio.com", "senha": "Admin@123"}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req).read().decode())
    token = resp["access_token"]
    print("1. [OK] LOGIN DO SINDICO REALIZADO. Token gerado com sucesso.")

    # 2. Test Audit Logs
    req_audit = urllib.request.Request(
        "http://127.0.0.1:8000/api/audit/logs",
        headers={"Authorization": f"Bearer {token}"}
    )
    logs = json.loads(urllib.request.urlopen(req_audit).read().decode())
    print(f"2. [OK] AUDITORIA DE SEGURANÇA: {len(logs)} eventos de acesso registrados.")
    for l in logs[:2]:
        print(f"   -> Data: {l['data_hora']} | Email: {l['email_informado']} | Sucesso: {l['sucesso']} | IP: {l['ip_origem']}")

    # 3. Test Notices
    req_notices = urllib.request.Request(
        "http://127.0.0.1:8000/api/notices",
        headers={"Authorization": f"Bearer {token}"}
    )
    notices = json.loads(urllib.request.urlopen(req_notices).read().decode())
    print(f"3. [OK] MURAL DE AVISOS: {len(notices)} comunicados encontrados.")

    # 4. Post New Notice
    new_notice = json.dumps({
        "titulo": "Assembleia Geral Ordinária de Condomínio",
        "mensagem": "Convocação geral dos condôminos para deliberação orçamentária e apresentação do relatório anual.",
        "categoria": "ASSEMBLEIA"
    }).encode()
    req_post = urllib.request.Request(
        "http://127.0.0.1:8000/api/notices",
        data=new_notice,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    )
    created = json.loads(urllib.request.urlopen(req_post).read().decode())
    print(f"4. [OK] PUBLICACAO DE AVISO: Novo aviso ID #{created['id']} criado com sucesso!")

    # 5. Verify RBAC on Audit for Morador
    morador_data = json.dumps({"email": "morador@condominio.com", "senha": "Morador@123"}).encode()
    req_morador = urllib.request.Request(
        "http://127.0.0.1:8000/api/auth/login",
        data=morador_data,
        headers={"Content-Type": "application/json"}
    )
    resp_morador = json.loads(urllib.request.urlopen(req_morador).read().decode())
    morador_token = resp_morador["access_token"]
    
    try:
        req_audit_forbidden = urllib.request.Request(
            "http://127.0.0.1:8000/api/audit/logs",
            headers={"Authorization": f"Bearer {morador_token}"}
        )
        urllib.request.urlopen(req_audit_forbidden)
        print("5. [FAIL] Morador nao deveria acessar auditoria!")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("5. [OK] RBAC VALIDADO: Morador recebeu 403 Forbidden ao tentar acessar auditoria (LGPD/Seguranca comprovada).")
        else:
            print(f"5. [WARN] HTTP Error: {e.code}")

if __name__ == "__main__":
    run_tests()
