@echo off
title Configurar Firewall para o WebApp (Porta 5000)
color 0B

echo ============================================================
echo   ⚡ LIBERANDO PORTA 5000 NO WINDOWS FIREWALL DO SERVIDOR
echo ============================================================
echo.

netsh advfirewall firewall add rule name="Clube Altera Dados WebApp (Porta 5000)" dir=in action=allow protocol=TCP localport=5000

if %errorlevel% equ 0 (
    echo.
    echo [SUCESSO] Porta 5000 liberada com sucesso no Firewall!
    echo Agora qualquer computador na rede local/AD consegue acessar o WebApp.
) else (
    echo.
    echo [ERRO] Execute este arquivo clicando com o BOTAO DIREITO -^> "Executar como Administrador".
)

echo.
pause
