@echo off
echo ===================================================
echo   Haruko 2.5 Update: Memory & LLM Hierarchy
echo ===================================================
echo.
echo Ziel-Verzeichnis: C:\KI\moltbotback\backend
echo.

if not exist "C:\KI\moltbotback\backend" (
    echo FEHLER: Zielverzeichnis nicht gefunden!
    echo Bitte stelle sicher, dass du auf dem Server bist.
    pause
    exit /b
)

echo Kopiere Dateien...
copy /Y memory_db.py "C:\KI\moltbotback\backend\"
copy /Y secretary.py "C:\KI\moltbotback\backend\"
copy /Y main.py "C:\KI\moltbotback\backend\"
copy /Y personality.py "C:\KI\moltbotback\backend\"
copy /Y .env "C:\KI\moltbotback\backend\"

echo.
echo ===================================================
echo   Update erfolgreich!
echo   Bitte starte 'start_backend.bat' neu.
echo ===================================================
pause
