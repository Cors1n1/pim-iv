from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings

# Configura proxies permitidos para cabeçalhos de encaminhamento
if "FORWARDED_ALLOW_IPS" not in os.environ:
    os.environ["FORWARDED_ALLOW_IPS"] = (settings.TRUSTED_PROXIES or "").strip()

from app.core.database import Base, engine
import app.models.condominio
import app.models.delivery
import app.models.guest
import app.models.notice
import app.models.reservation
import app.models.settings
import app.models.ticket
import app.models.user
import app.models.visitor
from app.routers import (
    audit,
    auth,
    console,
    deliveries,
    guests,
    notices,
    reservations,
    settings as condo_settings,
    superadmin,
    tickets,
    units,
    visitors,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Evento de inicialização
    print(f"[INICIANDO] {settings.PROJECT_NAME}")
    print("[BANCO] Conexao com banco de dados configurada em PostgreSQL")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("UPDATE usuarios SET precisa_trocar_senha = FALSE WHERE email = 'morador@condominio.com'"))
            await conn.execute(text("""
                ALTER TABLE condominios 
                ADD COLUMN IF NOT EXISTS slug VARCHAR(100) NULL,
                ADD COLUMN IF NOT EXISTS motivo_bloqueio VARCHAR(255) NULL,
                ADD COLUMN IF NOT EXISTS cor_sidebar VARCHAR(20) DEFAULT '#09090b',
                ADD COLUMN IF NOT EXISTS cor_fundo VARCHAR(20) DEFAULT 'AUTO',
                ADD COLUMN IF NOT EXISTS tipo_gestao VARCHAR(30) DEFAULT 'AUTOGESTAO',
                ADD COLUMN IF NOT EXISTS administradora_nome VARCHAR(150) NULL,
                ADD COLUMN IF NOT EXISTS administradora_email VARCHAR(150) NULL;
            """))
            await conn.execute(text("""
                UPDATE condominios 
                SET slug = LOWER(REGEXP_REPLACE(nome, '[^a-zA-Z0-9]+', '-', 'g')) 
                WHERE slug IS NULL OR slug = '';
            """))
            await conn.execute(text("""
                ALTER TABLE usuarios 
                ADD COLUMN IF NOT EXISTS condominio_id INT NULL,
                ADD COLUMN IF NOT EXISTS status_cadastro VARCHAR(30) DEFAULT 'ATIVO',
                ADD COLUMN IF NOT EXISTS token_convite VARCHAR(255) NULL,
                ADD COLUMN IF NOT EXISTS token_convite_expira_em TIMESTAMP WITH TIME ZONE NULL,
                ADD COLUMN IF NOT EXISTS token_version INT NOT NULL DEFAULT 1,
                ADD COLUMN IF NOT EXISTS cpf VARCHAR(20) NULL,
                ADD COLUMN IF NOT EXISTS precisa_trocar_senha BOOLEAN DEFAULT FALSE;
            """))
            await conn.execute(text("""
                ALTER TABLE areas_comuns 
                ADD COLUMN IF NOT EXISTS condominio_id INT DEFAULT 1,
                ADD COLUMN IF NOT EXISTS intervalo_dias_prioridade INT DEFAULT 30,
                ADD COLUMN IF NOT EXISTS max_reservas_ativas INT DEFAULT 2,
                ADD COLUMN IF NOT EXISTS prazo_standby_horas INT DEFAULT 48;
            """))
            await conn.execute(text("""
                ALTER TABLE reservas 
                ADD COLUMN IF NOT EXISTS prioridade VARCHAR(20) DEFAULT 'ALTA',
                ADD COLUMN IF NOT EXISTS prioridade_queimada BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS oferta_retomada_ate TIMESTAMP WITH TIME ZONE NULL,
                ADD COLUMN IF NOT EXISTS chave_entregue BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS chave_entregue_por INT NULL,
                ADD COLUMN IF NOT EXISTS chave_entregue_para VARCHAR(150) NULL,
                ADD COLUMN IF NOT EXISTS chave_entregue_em TIMESTAMP WITH TIME ZONE NULL,
                ADD COLUMN IF NOT EXISTS chave_devolvida BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS chave_devolvida_em TIMESTAMP WITH TIME ZONE NULL;
            """))
            await conn.execute(text("""
                ALTER TABLE configuracoes_condominio 
                ADD COLUMN IF NOT EXISTS condominio_id INT DEFAULT 1,
                ADD COLUMN IF NOT EXISTS dias_penalidade_queima INT DEFAULT 30;
            """))
            await conn.execute(text("""
                ALTER TABLE convidados_reserva 
                ALTER COLUMN documento DROP NOT NULL;
            """))
            await conn.execute(text("""
                ALTER TABLE convidados_reserva 
                ADD COLUMN IF NOT EXISTS convite_enviado BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS entrada_registrada BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS entrada_em TIMESTAMP WITH TIME ZONE NULL,
                ADD COLUMN IF NOT EXISTS saida_registrada BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS saida_em TIMESTAMP NULL;
            """))
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS configuracoes_plataforma (
                    id SERIAL PRIMARY KEY,
                    suporte_email VARCHAR(150) NOT NULL DEFAULT 'suporte@corsini.inf.br',
                    suporte_telefone VARCHAR(50) NOT NULL DEFAULT '(11) 98765-4321',
                    suporte_horario VARCHAR(100) DEFAULT 'Segunda a Sexta, das 08h às 18h',
                    titulo_regularizacao VARCHAR(150) DEFAULT 'O que fazer para regularizar?',
                    mensagem_regularizacao TEXT DEFAULT 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.',
                    titulo_suspensao VARCHAR(150) DEFAULT 'Acesso ao Condomínio Suspenso',
                    subtitulo_suspensao VARCHAR(255) DEFAULT 'O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central.',
                    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """))
            await conn.execute(text("""
                ALTER TABLE configuracoes_plataforma ALTER COLUMN mensagem_regularizacao TYPE TEXT;
            """))
            await conn.execute(text("""
                ALTER TABLE configuracoes_plataforma 
                ADD COLUMN IF NOT EXISTS titulo_regularizacao VARCHAR(150) DEFAULT 'O que fazer para regularizar?',
                ADD COLUMN IF NOT EXISTS titulo_suspensao VARCHAR(150) DEFAULT 'Acesso ao Condomínio Suspenso',
                ADD COLUMN IF NOT EXISTS subtitulo_suspensao VARCHAR(255) DEFAULT 'O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central.';
            """))
            await conn.execute(text("""
                INSERT INTO configuracoes_plataforma (id, suporte_email, suporte_telefone, suporte_horario, titulo_regularizacao, mensagem_regularizacao)
                VALUES (1, 'suporte@corsini.inf.br', '(11) 98765-4321', 'Segunda a Sexta, das 08h às 18h', 'O que fazer para regularizar?', 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.')
                ON CONFLICT (id) DO NOTHING;
            """))
            await conn.execute(text("""
                UPDATE configuracoes_plataforma
                SET mensagem_regularizacao = 'Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real.'
                WHERE mensagem_regularizacao IS NULL OR mensagem_regularizacao NOT LIKE '%•%';
            """))
            await conn.execute(text("""
                UPDATE configuracoes_plataforma
                SET titulo_regularizacao = 'O que fazer para regularizar?'
                WHERE titulo_regularizacao IS NULL;
            """))
        print("[BANCO] Tabelas sincronizadas e colunas operacionais migradas com sucesso.")
    except Exception as err:
        print(f"[BANCO] Aviso ao sincronizar esquema: {err}")
    yield
    # Evento de encerramento
    print(f"[FINALIZANDO] {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST modular para Gestão Integrada de Condomínios (SGC)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuração de CORS para permitir requisições do Frontend Web e Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.endswith((".html", ".js", ".css")) or path.startswith("/c/") or path in ("/", "/console", "/console/", "/superadmin", "/superadmin/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Middleware para inclusão de cabeçalhos HTTP de segurança."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

# Inclusão dos roteadores da aplicação
app.include_router(auth.router)
app.include_router(console.router)
app.include_router(superadmin.router)
app.include_router(units.router)
app.include_router(deliveries.router)
app.include_router(reservations.router)
app.include_router(guests.router)
app.include_router(tickets.router)
app.include_router(visitors.router)
app.include_router(notices.router)
app.include_router(condo_settings.router)
app.include_router(audit.router)


@app.get("/health", tags=["Status"])
async def health_check() -> dict:
    """Endpoint de verificação de integridade da API."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "database": "PostgreSQL conectado",
        "version": "1.0.0"
    }


# Montagem do Frontend
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
console_dir = os.path.join(frontend_dir, "console")
superadmin_dir = os.path.join(frontend_dir, "superadmin")

# Monta o Console de Operações da Diretoria CondoHub
if os.path.exists(console_dir):
    app.mount("/console", StaticFiles(directory=console_dir, html=True), name="console")

# Mantém rota legada com redirecionamento automático
if os.path.exists(superadmin_dir):
    app.mount("/superadmin", StaticFiles(directory=superadmin_dir, html=True), name="superadmin")

# Rotas de acesso de ativação (Universal e por Condomínio)
@app.get("/ativar", tags=["Frontend"])
@app.get("/ativar/", tags=["Frontend"])
@app.get("/c/{slug}/ativar", tags=["Frontend"])
@app.get("/c/{slug}/ativar/", tags=["Frontend"])
async def serve_condominio_activation(slug: Optional[str] = None):
    """Serve o assistente responsivo de primeiro acesso e ativação do síndico."""
    ativar_file = os.path.join(frontend_dir, "ativar.html")
    if os.path.exists(ativar_file):
        return FileResponse(ativar_file)
    raise HTTPException(status_code=404, detail="Assistente de ativação não encontrado.")

@app.get("/ativar-morador", tags=["Frontend"])
@app.get("/ativar-morador/", tags=["Frontend"])
@app.get("/c/{slug}/ativar-morador", tags=["Frontend"])
@app.get("/c/{slug}/ativar-morador/", tags=["Frontend"])
async def serve_resident_activation(slug: Optional[str] = None):
    """Serve a página responsiva de auto-cadastro e ativação do morador convidado."""
    file_path = os.path.join(frontend_dir, "ativar_morador.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Página de ativação não encontrada.")

@app.get("/c/{slug}", tags=["Frontend"])
@app.get("/c/{slug}/", tags=["Frontend"])
async def serve_condominio_app(slug: str):
    """Serve a aplicação modular personalizada com a identidade do condomínio."""
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Aplicação não encontrada.")


# Monta o Portal dos Condomínios na raiz
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

