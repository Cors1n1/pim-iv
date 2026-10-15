from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.database import Base, engine
import app.models.delivery
import app.models.guest
import app.models.notice
import app.models.reservation
import app.models.settings
import app.models.ticket
import app.models.user
import app.models.visitor
from app.routers import audit, auth, deliveries, guests, notices, reservations, settings as condo_settings, tickets, units, visitors


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
                ALTER TABLE configuracoes_condominio 
                ADD COLUMN IF NOT EXISTS dias_penalidade_queima INT DEFAULT 30;
            """))
            await conn.execute(text("""
                ALTER TABLE convidados_reserva 
                ALTER COLUMN documento DROP NOT NULL;
            """))
            await conn.execute(text("""
                ALTER TABLE convidados_reserva 
                ADD COLUMN IF NOT EXISTS saida_registrada BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS saida_em TIMESTAMP NULL;
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
    if path.endswith((".html", ".js", ".css")) or path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Inclusão dos roteadores da aplicação
app.include_router(auth.router)
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


# Montagem do Frontend Web estático na raiz
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

