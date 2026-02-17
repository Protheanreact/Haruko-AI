# MoltBot (Haruko) Technical Guidelines

## Architektur Übersicht
Das System besteht aus zwei Hauptkomponenten:
1. **Backend (Python/FastAPI)**: Läuft auf Port 8000. Steuert Logik, KI, TTS und Systemzugriff.
2. **Frontend (React/Vite)**: Läuft auf Port 5173. Dient als UI, Visualisierung (Avatar) und Spracheingabe.

## Wichtige Module
- **main.py**: Einstiegspunkt. Definiert API-Endpunkte und den zentralen Loop.
- **secretary.py**: Verwaltet Timer, Notizen und Hintergrundaufgaben.
- **vision.py**: Zuständig für Bildanalyse (Webcam/Screenshot) und FaceID.
- **phygital.py**: Steuert Tuya Smart Home Geräte und reagiert auf Sensordaten.
- **tts_cli.py**: Isoliertes Skript für Sprachausgabe (Edge-TTS), um den Main-Loop nicht zu blockieren.

## Coding Conventions
- **Asynchron**: Nutze immer `async def` für Endpunkte und I/O-Operationen.
- **Tools**: Wenn die KI eine Aktion ausführen soll, nutze das `EXECUTE:` Prefix.
- **Sicherheit**: Keine API-Keys hardcoden, nutze `.env`.

## Fehlerbehebung
- **Port belegt**: Prüfe mit `netstat -ano | findstr :8000`, welcher Prozess den Port blockiert.
- **CORS Fehler**: Stelle sicher, dass `vite.config.ts` den Proxy korrekt auf `http://127.0.0.1:8000` leitet.