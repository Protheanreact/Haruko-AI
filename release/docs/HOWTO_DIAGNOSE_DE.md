# How-To: Server Diagnose & Reparatur

## Einführung
Da das Haruko-System immer komplexer wird (neue KI-Modelle, externe APIs wie Groq/Gemini, lokale Dienste wie Ollama), kann es vorkommen, dass nach einem Update oder Server-Umzug etwas fehlt.

Dafür gibt es jetzt das **Server Diagnose Tool** (`server_diagnose_fix.py`).

## Wann sollte ich das nutzen?
- Nach jedem Update (wenn du neue Dateien auf den Server kopiert hast).
- Wenn Fehler im Terminal auftauchen (z.B. `ModuleNotFoundError`, `Model not found`).
- Wenn Haruko nicht antwortet.
- Wenn du den Server neu aufsetzt.

## Anleitung

1. **Terminal öffnen**
   Navigiere in den `backend` Ordner deiner Installation.
   ```powershell
   cd C:\moltbotback\backend
   ```

2. **Tool starten**
   Führe das Python-Skript aus:
   ```powershell
   python server_diagnose_fix.py
   ```

3. **Ausgabe verstehen**
   Das Tool durchläuft 5 Phasen:
   
   - **1. PYTHON CHECK**: Prüft, ob Python aktuell genug ist.
   - **2. DEPENDENCY CHECK**: Prüft alle installierten Bibliotheken (`requirements.txt`).
     - *Aktion*: Wenn etwas fehlt (z.B. `groq`), wird es **automatisch installiert**.
   - **3. OLLAMA CHECK**: Prüft, ob der lokale KI-Dienst läuft.
     - *Aktion*: Prüft, ob die Modelle `llama3.1` und `llava` vorhanden sind.
     - *Aktion*: Wenn ein Modell fehlt, wird es **automatisch heruntergeladen** (Download-Balken erscheint).
   - **4. ENV CHECK**: Prüft, ob die `.env` Datei und die API-Keys vorhanden sind.
   - **5. API TEST**: Versucht tatsächlich, die Cloud-KIs (Groq & Gemini) zu erreichen.
     - *Erfolg*: "✅ Groq Connection SUCCESS"
     - *Fehler*: Zeigt genau an, was falsch ist (z.B. falscher Key, Quota erreicht).

4. **Abschluss**
   Wenn das Tool am Ende "DIAGNOSTICS COMPLETE" anzeigt und überall grüne Haken (✅) sind, ist dein System zu 100% bereit.
   Du kannst dann `python main.py` starten.

## Häufige Fehler & Lösungen

- **Download hängt**: Der Download der KI-Modelle (ca. 5GB) kann dauern. Nicht abbrechen!
- **API Test Failed**: Prüfe deine Internetverbindung. Wenn Internet da ist, überprüfe die Keys in der `.env` Datei.
- **Permission Error**: Führe das Terminal als Administrator aus, falls Installationen fehlschlagen.
