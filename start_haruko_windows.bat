@echo off
title Haruko Launcher
color 0A
cd /d "%~dp0"
echo ===================================================
echo    HARUKO AI SERVER - STARTUP SCRIPT (WINDOWS)
echo ===================================================
echo.

:: 0. Cleanup old processes
echo [0/3] Bereinige alte Prozesse...
taskkill /F /IM python.exe /T 2>NUL
taskkill /F /IM node.exe /T 2>NUL
echo   - Alte Prozesse beendet.
echo.

:: 1. Check Ollama
echo [1/3] Pruefe KI-Engine (Ollama)...
tasklist /FI "IMAGENAME eq ollama app.exe" 2>NUL | find /I /N "ollama app.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo   - Ollama laeuft bereits.
) else (
    echo   - Starte Ollama im Hintergrund...
    start "" "ollama" serve
)

:: 2. Start Backend
echo [2/3] Starte Backend Server...
:: Wir rufen jetzt ein dediziertes Skript im Backend-Ordner auf
start "Haruko Backend" cmd /k "cd backend && call start_backend.bat"

echo.
echo Warte 5 Sekunden auf Backend-Initialisierung...
timeout /t 5 /nobreak >NUL

:: 3. Start Frontend

echo [3/3] Starte Frontend (Webseite)...
:: --host 0.0.0.0 macht es im Netzwerk verfuegbar
start "Haruko Frontend" cmd /k "cd frontend && npm run dev -- --host 0.0.0.0"

:: 4. Start Internet Tunnel (Optional)
echo.
echo [4/4] Internet Zugriff (Optional)
echo       Fuer Remote-Zugriff bitte Port 5173 und 8000 im Router freigeben!

echo.
echo ===================================================
echo    HARUKO LAEUFT!
echo ===================================================
echo.
echo Zugriff von diesem PC:
echo   - http://localhost:5173
echo.
echo Zugriff aus dem Netzwerk/Internet:
echo   - http://DEINE_IP_ODER_DOMAIN:5173
echo.
echo (Backend API: http://DEINE_IP_ODER_DOMAIN:8000)
echo.
pause
