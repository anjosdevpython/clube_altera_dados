@echo off
title Servidor WebApp Clube Altera Dados - Servidor AD
color 0A

echo ============================================================
echo   ⚡ INICIANDO SERVIDOR WEBAPP CLUBE ALTERA DADOS (PORTA 5000)
echo ============================================================
echo.

python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [AVISO] Falha ao instalar dependencias com python padrao. Tentando com py...
)

python server.py

pause
