@echo off
chcp 65001 >nul
title SGC - Sistema de Gestao de Condominio - Residencial Bela Vista

echo ====================================================================
echo   SISTEMA DE GESTAO DE CONDOMINIO (SGC) - RESIDENCIAL BELA VISTA
echo ====================================================================
echo.
echo [1/3] Verificando instalacao do Python...
py -3 --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [ERRO] Python nao foi encontrado no sistema.
        echo Instale o Python ou adicione-o ao PATH do Windows.
        pause
        exit /b 1
    )
    set PY_CMD=python
) else (
    set PY_CMD=py -3
)

echo [2/3] Abrindo a interface web no seu navegador...
start "" "http://localhost:8000"

echo [3/3] Iniciando o servidor Backend (FastAPI + PostgreSQL)...
echo.
echo ====================================================================
echo   PAINEL DE ACESSO:
echo   - Interface Web (Sistema):     http://localhost:8000
echo   - Documentacao Swagger (APIs): http://localhost:8000/docs
echo   - Verificacao de Integridade:  http://localhost:8000/health
echo ====================================================================
echo   Pressione CTRL + C a qualquer momento para parar o servidor.
echo ====================================================================
echo.

cd /d "%~dp0backend"
%PY_CMD% -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --forwarded-allow-ips="" --reload
