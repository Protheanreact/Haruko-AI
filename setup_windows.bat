@echo off
title Haruko Setup
color 0B
cd /d "%~dp0"
echo ===================================================
echo    HARUKO - INSTALLATION (WINDOWS)
echo ===================================================
echo.
echo Dieses Skript installiert alles automatisch:
echo  1. Python Module (Backend)
echo  2. Node.js Module (Frontend)
echo  3. Ollama & KI-Modelle (Llama 3, Vision)
echo  4. Internet-Tunnel Tools
echo.
echo Bitte sicherstellen, dass du Internet hast.
echo.
pause

echo Starte Installations-Skript (PowerShell)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_haruko_aio.ps1"

echo.
if %ERRORLEVEL% EQU 0 (
    echo [OK] Installation abgeschlossen.
    echo Du kannst nun 'start_haruko_windows.bat' nutzen.
) else (
    echo [FEHLER] Irgendwas lief schief. Siehe oben.
)
pause
