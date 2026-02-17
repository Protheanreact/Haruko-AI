@echo off
cd /d "%~dp0"
if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [WARNUNG] Kein VENV gefunden! Versuche globale Python-Installation...
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [FEHLER] Python ist nicht installiert oder nicht im PATH!
        pause
        exit
    )
)
echo [INFO] Starte Main Server...
python main.py
pause