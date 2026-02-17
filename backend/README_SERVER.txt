ANLEITUNG FÜR DEN SERVER-CHECK
==============================

Um sicherzustellen, dass auf dem Fujitsu-Server alles läuft (und um Probleme automatisch zu beheben), habe ich ein Diagnose-Skript erstellt.

Schritte:

1. Dateien aktualisieren:
   Lade die neuesten Dateien auf den Server (besonders 'requirements.txt', '.env', 'main.py' und das neue 'server_diagnose_fix.py').

2. Diagnose starten:
   Öffne ein Terminal (PowerShell oder CMD) im Ordner 'backend'.
   Führe folgenden Befehl aus:

   python server_diagnose_fix.py

3. Was macht das Skript?
   - Prüft Python-Version.
   - Prüft alle Pakete (installiert fehlende automatisch nach, z.B. 'groq').
   - Prüft Ollama (ob es läuft und ob 'llama3.1' und 'llava' da sind -> lädt sie sonst herunter).
   - Prüft die .env Datei (ob Keys da sind).
   - Testet die Verbindung zu Groq und Gemini (mit echten API-Calls).

4. Starten:
   Wenn alles "✅" zeigt, kannst du den Bot ganz normal starten:

   python main.py

HINWEIS:
Falls Ollama Modelle fehlen (z.B. 'llama3.1'), wird der Download automatisch gestartet. Das kann je nach Internet ein paar Minuten dauern.
