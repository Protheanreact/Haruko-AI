# Technisches Handbuch - Haruko AI v2.8

## Übersicht
Haruko AI ist ein modularer KI-Assistent mit 3D-Avatar, Sprachsteuerung, Smart-Home-Integration (Tuya) und einem modernen Web-Interface. Das System besteht aus einem Python-Backend (FastAPI) und einem React-Frontend (Vite).
**Version 2.8 führt vollständige Mehrsprachigkeit (Deutsch/Englisch) ein.**

## Architektur

### System-Diagramm (Haruko 2.6)

```mermaid
graph TD
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef backend fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef cloud fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef hardware fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px;

    %% User Layer
    User((User)) -->|Sprache/Text| UI[Frontend UI\n(React/Vite)]
    User -->|Kamera| VisionCam[MobileVision\n(WebRTC)]
    User -->|Telegram| TeleBot
    
    %% Frontend Layer
    subgraph Frontend [Frontend Layer (Browser / Tablet)]
        direction TB
        UI -->|Rendert| Avatar[3D Avatar\n(VRM / Three.js)]
        UI -->|Sendet Audio/Text| API_Client[Axios / Fetch]
        VisionCam -->|Postet Frames| API_Client
    end
    
    %% Backend Layer
    subgraph Backend [Backend Layer (Python / FastAPI)]
        direction TB
        API_Gateway[API Gateway\n(main.py)]
        
        %% Core Logic
        Brain[LLM Logic / Router]
        Personality[Personality Engine\n(System Prompts)]
        WakeWord[Wake Word Listener\n(Vosk Local)]
        
        %% Submodules
        VisionMod[Vision Module\n(FaceID / Analysis)]
        Secretary[Secretary Module\n(Timer/Notes/Weather)]
        PC_Control[PC Control\n(App Launcher / Audio)]
        TuyaMod[Tuya Smart Home\n(tinytuya)]
        AutoLoop[Autonomous Loop\n(Boredom/Phygital)]
        
        %% Connections
        API_Gateway --> Brain
        API_Gateway --> VisionMod
        API_Gateway --> Secretary
        API_Gateway --> PC_Control
        API_Gateway --> TuyaMod
        
        Brain --> Personality
        AutoLoop --> Brain
        WakeWord --> API_Gateway
        
        %% New Modules v2.7
        NetTools[Network Tools\n(Wake-on-LAN)]
        SelfLearn[Self-Learning\n(Gemini Generator)]
        
        API_Gateway --> NetTools
        API_Gateway --> SelfLearn
    end
    
    %% Cloud Services
    subgraph CloudServices [External / Cloud Services]
        GeminiFree[Gemini 2.0 Flash\n(Free Key - Primär)]
        Groq[Groq API\n(Llama 3 70B - Sekundär)]
        OpenRouter[OpenRouter\n(Free Models - Tertiär)]
        GeminiPaid[Gemini 2.0 Flash\n(Paid Key - Backup)]
        Ollama[Ollama\n(Local Fallback)]
        TTS_Cloud[Edge-TTS\n(Neural Voices)]
        Search[DuckDuckGo\n(Pre-Search)]
        TeleBot[Telegram Bot\n(Remote Control)]
    end
    
    %% Storage Layer
    subgraph Storage [Data & Memory]
        MemDB[(Long-Term Memory\nJSON/SQLite)]
        RAG[(RAG Knowledge\nPDFs)]
        Faces[(Known Faces\nImages)]
    end

    %% Data Flow Interactions
    API_Client <-->|HTTP / WebSocket| API_Gateway
    TeleBot <-->|Thread| API_Gateway
    
    %% Backend to Cloud
    Brain -->|1. Request| GeminiFree
    Brain -->|2. Fallback| Groq
    Brain -->|3. Fallback| OpenRouter
    Brain -->|4. Backup| GeminiPaid
    Brain -->|5. Offline| Ollama
    Brain -->|Search Info| Search
    
    %% Backend to Storage
    Brain <--> MemDB
    Brain <--> RAG
    VisionMod <--> Faces
    
    %% Backend to Output
    API_Gateway -->|Generate Audio| TTS_Cloud
    TTS_Cloud -->|Audio Stream| UI
    
    %% Hardware Control
    TuyaMod -->|Cloud/Local| SmartHome[Smart Home Devices]
    PC_Control -->|OS Calls| Windows[Windows OS]

    %% Classes
    class UI,Avatar,VisionCam,API_Client frontend;
    class API_Gateway,Brain,Personality,VisionMod,Secretary,PC_Control,TuyaMod,WakeWord,AutoLoop backend;
    class Groq,Gemini,Ollama,TTS_Cloud,Search,TeleBot cloud;
    class MemDB,RAG,Faces storage;
    class SmartHome,Windows hardware;
```

### Backend (Python/FastAPI)
Das Backend läuft unter `main.py` und stellt REST-API-Endpunkte sowie WebSocket-Streams bereit.
- **Framework**: FastAPI (High Performance, Async).
- **KI-Architektur (Hybrid)** - Neue Hierarchie (Stand 2026):
  - *Primär*: **Gemini Free** (Flash 2.0) - Höchste Priorität für generelle Anfragen (Key D).
  - *Sekundär*: **Groq (Llama 3 70B)** - Extrem schnelle Textgenerierung (nahezu Latenzfrei).
  - *Tertiär*: **OpenRouter (Free Models)** - Fallback auf diverse kostenlose Modelle (DeepSeek, Qwen, etc.).
  - *Notfall-Backup*: **Gemini Paid** (Flash 2.0) - Bezahlter Key (Key C) nur wenn alles andere fehlschlägt.
  - *Offline-Fallback*: **Ollama** (Lokal, z.B. Llama 3.1) bei komplettem Internet-Ausfall.
- **API-Keys**: Werden sicher in der `.env` Datei verwaltet (Keys: `GEMINI_API_KEY_FREE`, `GEMINI_API_KEY_PAID`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`).
- **Persönlichkeit**: Haruko nutzt einen neuen, sarkastischen Persona-Prompt (definiert in `personality.py`). 
  - *Stil*: "Anime/Tsundere" - frech, emotional, nutzt Emojis.
  - *Besonderheit*: Der System-Prompt ist auf Englisch (für besseres Verständnis der KI), die Antworten erfolgen jedoch strikt auf Deutsch.
  - *Emojis*: Werden im Chat angezeigt, aber von der TTS ignoriert (siehe oben).
- **Spracherkennung (STT)**:
  - *Lokal*: Vosk (Offline) als Standard.
- **Sprachausgabe (TTS)**: 
  - *Engine*: Edge-TTS (Online, High Quality Neural Voices).
  - *Tuning*: Spezielles "Anime/Waifu"-Tuning (Pitch +25Hz, Rate +10%) für lebendigere Stimme.
  - *Filter*: Automatisches Stripping von Emojis und Sonderzeichen. Haruko kann im Chat Emojis nutzen ("Hi! 😊"), aber die TTS liest diese nicht vor ("Hi!"), um den Sprachfluss natürlich zu halten.
- **Smart Home**: `tinytuya` zur Steuerung von Tuya-Geräten im lokalen Netzwerk oder über die Cloud.
- **Tools & Agenten**:
  - *Pre-Search*: Automatische Websuche (DuckDuckGo) bei Wissensfragen vor der LLM-Generierung.
  - *Sekretär*: Timer, Wecker, Notizen, Wetter (Open-Meteo).
  - *Vision*: Analyse von Webcam-Bildern oder Screen-Sharing (via Gemini oder lokalem Llava).

### Vision & FaceID Subsystem
Das System verfügt über fortgeschrittene visuelle Fähigkeiten, implementiert als Hybrid-Lösung (Client-Push + Backend-Processing):
1.  **Client-Side Capture (`MobileVision.tsx`)**:
    - Nutzt die HTML5 `getUserMedia` API, um auf die Kamera (Smartphone/Webcam) zuzugreifen.
    - Sendet alle 5 Sekunden (konfigurierbar) Frames an `/api/vision/analyze`.
2.  **Face Recognition (`vision.py`)**:
    - Verwendet `face_recognition` (dlib) zur Identifikation bekannter Personen.
    - Referenzbilder liegen in `backend/known_faces/` (z.B. `Jenny.jpg`).
    - Encodings werden gecacht (`FACE_CACHE`), um die CPU-Last zu minimieren.
3.  **Generative Vision**:
    - Bei Befehlen wie "Was siehst du?" wird der aktuelle Frame (Webcam oder Screenshot via `mss`) an das Multimodal-Modell (Gemini 2.0 Flash) gesendet.
    - Der Prompt fordert eine Beschreibung aus der Perspektive des Avatars.

### Frontend (React/TypeScript)
Das Frontend ist eine Single-Page-Application (SPA), die mit Vite gebuildet wird.
- **Framework**: React 19.
- **Sprache**: TypeScript.
- **3D-Avatar**: `@pixiv/three-vrm` und `@react-three/fiber` zur Darstellung von VRM-Modellen.
- **Animationen**: Neu in v2.9: Nutzung von `@pixiv/three-vrm-animation` für native `.vrma` Dateien (statt FBX).
- **Kommunikation**: Axios für API-Requests, Fetch API für Streaming-Responses.
- **UI-Logik**: 
  - Trennung von *Anzeige* und *interner Verarbeitung*.
  - `EXECUTE:`-Befehle (die Haruko zur Steuerung nutzt) werden vom Frontend empfangen und ausgeführt, aber per Regex aus der Chat-Blase entfernt. Der User sieht nur die natürliche Antwort.
- **Design**: Benutzerdefiniertes CSS (Glassmorphismus), Lucide-Icons.

## Kernkomponenten & Datenfluss

1.  **Spracheingabe**:
    - *Frontend*: Das Mikrofon wird über die MediaRecorder API abgegriffen. Audio-Blobs (WebM) werden an `/process_audio` gesendet.
    - *Backend*: `ffmpeg` konvertiert WebM zu WAV. Vosk oder Google Speech transkribiert das Audio zu Text.

2.  **Verarbeitung (Brain)**:
    - **Pre-Search**: Prüft, ob aktuelle Informationen nötig sind (z.B. "Wetter", "News"). Falls ja, wird eine Websuche durchgeführt und das Ergebnis in den Kontext injiziert.
    - **Hybrid-Generierung**:
      1. Versuch: Anfrage an Gemini API (schnell, smart).
      2. Fallback: Bei Fehler/Quota-Limit übernimmt automatisch das lokale Ollama-Modell.
    - Ein Prompt-Template (in `personality.py`) definiert den Charakter des Bots.

3.  **Antwort & Avatar**:
    - Der Text wird via Server-Sent Events oder direktem Response an das Frontend gesendet.
    - Das Frontend triggert `/speak`. Backend generiert Audio mit **Edge-TTS** (getuned).
    - Der Avatar (`VRMAvatar.tsx`) analysiert die Lautstärke/Vokale und bewegt den Mund (Lip-Sync).

4.  **Smart Home**:
    - Befehle wie "Licht an" werden per Regex im Backend erkannt.
    - `TuyaManager` (in `main.py`) sendet Befehle an die Tuya Cloud oder lokal an die Geräte-IP.

## Wichtige Dateien
- `backend/main.py`: Haupteinstiegspunkt, API-Routen, WebSocket, Audio-Verarbeitung.
- `backend/secretary.py`: Hilfsfunktionen für Wetter, Notizen, Timer.
- `frontend/src/App.tsx`: Hauptlogik der UI, State-Management, Audio-Aufnahme.
- `frontend/src/components/VRMAvatar.tsx`: 3D-Rendering, Animationen, Wetter-Reaktivität.
  - **Setup Mode (Neu in v2.9)**: Interaktiver Modus (**Shift+S**) zum Positionieren von Möbeln (Stuhl, Bett) im 3D-Raum via Gizmos.
  - **Animation System**: Hybrid-System aus `.vrma` Base-Layers (Sitzen, Schlafen) und prozeduralen Gesten (Winken, Nicken), die via `THREE.AnimationMixer` geblendet werden.
  - **Mood-System**: Nutzt `THREE.MathUtils.lerp` für flüssige Übergänge zwischen emotionalen Posen (Happy, Angry, etc.), gesteuert durch `[MOOD:...]` Tags vom Backend.

## Konfiguration
- **Frontend**: `.env` Datei für die API-URL (`VITE_API_URL`).
- **Backend**: `TUYA_ACCESS_ID` und `TUYA_ACCESS_SECRET` in `main.py` für Smart Home.

## 7. Sekretär & Gedächtnis (Memory 3.0)
Das System verfügt über ein erweitertes Langzeitgedächtnis (LTM), das auf **SQLite** basiert (`memory.db`), um Datenverlust zu vermeiden und Skalierbarkeit zu gewährleisten.
- **Speicher**: SQLite Datenbank (`backend/memory.db`).
- **User Profiler (Neu in v2.10)**:
  - Eine spezialisierte Komponente (`user_profiler.py`), die dynamische psychologische Profile der Nutzer erstellt.
  - Speichert Attribute (z.B. "Mag Sarkasmus", "Interessiert an Tech", "Stimmung: Gestresst") als JSON in der Tabelle `user_profiles`.
  - Diese Daten werden bei jedem Gesprächsbeginn (basierend auf FaceID) in den System-Prompt geladen, sodass Haruko sich perfekt auf das Gegenüber einstellt.
- **Reflexion (Memory Maintenance)**: 
  - Ein automatischer Hintergrund-Prozess (`perform_memory_reflection` in `main.py`) prüft alle 24 Stunden den Wissensbestand.
  - Alle Fakten werden an Gemini Pro gesendet, um Duplikate zu entfernen, ähnliche Fakten zusammenzufassen und Veraltetes zu löschen.
  - Dies hält das Gedächtnis kompakt und relevant, ohne manuelles Eingreifen.
- **Migration**: Ein automatisches Migrations-Skript (`memory_db.py`) wandelt alte `secretary_data.json` Dateien beim Start in die Datenbankstruktur um.
- **Funktionen**:
  - **Fakten (LTM)**: `EXECUTE: memory --add "..."` speichert User-Präferenzen dauerhaft.
  - **Auto-Memory (Neu in v2.6)**: Haruko analysiert Gespräche automatisch auf wichtige Fakten (z.B. "Ich mag Pizza") und speichert diese selbstständig, ohne expliziten Befehl.
  - **RAG-Suche (Neu in v2.6)**: Haruko kann aktiv in ihrem Gedächtnis suchen (`search_memory`), um komplexe Fragen zu beantworten ("Was weißt du über meine Hobbys?").
  - **Notizen**: Logbuch für Gedanken/Aufgaben.
  - **Timer & Wecker**: Hintergrund-Loop in `main.py` prüft minütlich auf fällige Zeitstempel.

## 8. Autonomie & Netzwerk (Neu in v2.7)
Mit Version 2.7 erreicht Haruko eine neue Ebene der Selbstständigkeit.
- **Self-Learning (Auto-Knowledge)**:
  - Haruko kann Wissenslücken selbstständig schließen.
  - Erkennt der Bot eine Lern-Anforderung (z.B. "Lern mir Quantenphysik"), startet er eine **Gemini-Recherche**.
  - Die Ergebnisse werden strukturiert, als Markdown formatiert ("Leitfaden") und im `knowledge/` Ordner abgelegt.
  - **Auto-Indexing**: Das neue Wissen wird sofort indiziert und steht für zukünftige RAG-Abfragen bereit.
- **Netzwerk-Kontrolle (Network Tools)**:
  - Integration der `network_tools` Bibliothek.
  - **Wake-on-LAN**: Haruko kann PCs im lokalen Netzwerk aufwecken (`EXECUTE: WAKE_PC [MAC]`).
  - Dies geschieht über UDP Broadcast (Magic Packet) und benötigt keine Admin-Rechte auf dem Zielrechner, nur BIOS-Support (WoL enabled).
- **PDF-Diagnose**:
  - `debug_pdf.py`: Ein Tool zur Analyse von PDF-Dateien. Es prüft, ob Text extrahierbar ist oder ob es sich um reine Bilder (Scans) handelt, um "blinde Flecken" im Wissen zu vermeiden.
  - **Wetter**: Integration von Open-Meteo API.

## 8. PC-Steuerung & App-Launcher (`pc_control.py`)
Haruko hat tiefen Zugriff auf das Host-System (Windows):
- **Audio**: Steuerung der Systemlautstärke via `pycaw` (Core Audio Windows Library).
- **App-Launcher**: Mapping von Keywords zu Exe-Pfaden oder Protokollen:
  - `spotify` -> `spotify.exe`
  - `steam` -> `steam.exe`
  - `cyberpunk` -> `steam://run/1091500`
  - `yi` / `yi iot` -> Yi IoT Client (für Kameras).
- **System**: Shutdown, Reboot, Lock Screen via `os.system`.

## 9. Telegram Bot Integration (`telegram_bot.py`)
Ein voll-asynchroner Telegram-Bot (basierend auf `python-telegram-bot`) ermöglicht Fernsteuerung:
- **Architektur**: Läuft in eigenem `asyncio` Loop parallel zu FastAPI.
- **Features**:
  - **Chat**: Nachrichten werden an das gleiche LLM-Gehirn geleitet (getrennter Kontext).
  - **Vision**: Befehl `/cam` sendet ein aktuelles Foto der Webcam oder des Bildschirms an den Telegram-Chat.
  - **Token**: Hardcodiert oder via Env-Var konfigurierbar.

## 10. Client-Steuerung & Tablet-Bridge (ADB)
Damit Haruko auch Aktionen auf dem Endgerät (Tablet/Handy) ausführen kann, gibt es zwei Wege:

### A. Frontend Bridge (Browser)
- **Konzept**: Das Backend sendet Befehle im Antwort-Text, die das Frontend abfängt und lokal ausführt.
- **Protokoll**: `EXECUTE_CLIENT: [BEFEHL]|[PARAMETER]`
- **Unterstützte Befehle**:
  - `open_url|URL`: Öffnet einen neuen Tab.
  - `scroll|down` / `scroll|up`: Scrollt die Haruko-App selbst.
  - `alert|Text`: System-Popup.

### B. ADB Bridge (Android Native Control)
Für Aktionen **außerhalb** des Browsers (z.B. TikTok App steuern) nutzt Haruko die Android Debug Bridge (ADB).
- **Setup**: `setup_adb.bat` verbindet den Server (PC) mit dem Tablet via TCP/IP.
- **Funktionsweise**:
  - Haruko sendet Shell-Befehle an das verbundene Gerät.
  - Befehl: `adb shell input swipe 500 1500 500 500 300` (Simuliert Wisch-Geste nach oben).
- **Vorteil**: Ermöglicht Steuerung JEDER App (TikTok, Kindle, YouTube), solange das Tablet gekoppelt ist.

## 11. Externe Integration (Notifications API)
Um Haruko auf Benachrichtigungen von externen Apps (z.B. WhatsApp, Email) reagieren zu lassen, wurde eine REST-API-Schnittstelle geschaffen. Diese kann von Automatisierungs-Apps wie **MacroDroid** oder **Tasker** genutzt werden.

### Endpunkt
- **URL**: `POST /api/notify`
- **Body (JSON)**:
  ```json
  {
    "app": "WhatsApp",
    "title": "Mama",
    "message": "Kommst du heute zum Essen?",
    "priority": "normal"
  }
  ```

### Integration mit MacroDroid
1. **Auslöser**: "Benachrichtigung empfangen" (z.B. WhatsApp).
2. **Aktion**: "HTTP Request" (HTTP Anfrage).
   - **Methode**: `POST`
   - **URL**: `https://mein-haruko.ddnss.de:5173/api/notify`
   - **Parameter abfragen**: (Leer lassen)
   - **Header Parameter**:
     - Klicke auf **+** (Hinzufügen).
     - Es erscheinen zwei Felder. Diese musst du **selbst ausfüllen**:
       - *Parameter-Name* (oder Name): Tippe hier `Content-Type` ein.
       - *Wert*: Tippe hier `application/json` ein.
   - **Inhaltskörper**:
     - *Inhaltstyp*: `application/json` (oder Text/Raw)
     - *Text/Inhalt*: `{"app": "WhatsApp", "title": "{not_title}", "message": "{not_text_big}"}`
3. **Funktionsweise**:
   - Haruko empfängt die Nachricht.
   - Haruko liest die Nachricht via TTS vor ("Nachricht von WhatsApp...").
   - Lange Nachrichten werden nach 200 Zeichen gekürzt.

## 12. WhatsApp Web Bridge (Inoffiziell, lokal)
Neben der Notifications-API existiert eine lokale WhatsApp-Web-Bridge, die direkte Chats mit Haruko über WhatsApp ermöglicht, ohne Meta-Cloud-API.

### Architektur
- **Bridge-Prozess (Node.js)**:
  - Pfad (Empfehlung): `C:\KI\haruko-whatsapp-bridge\haruko-whatsapp.js`.
  - Bibliotheken: `whatsapp-web.js`, `qrcode-terminal`, `axios`, `puppeteer` (Chrome).
  - Login über QR-Code, Session-Persistenz via `LocalAuth`.
- **Backend-Integration (FastAPI)**:
  - `GET /whatsapp/health` – einfacher Health-Check.
  - `POST /whatsapp/incoming` – nimmt Nachrichten von der Bridge entgegen und ruft intern `process_chat_generator` auf.
  - Rückgabe: `{ "reply": "<Text, der an WhatsApp zurückgeschickt werden soll>" }`.

### Sicherheitskonzept & Routing
- **Master-Nummer**:
  - Im Bridge-Skript als `MASTER_NUMBER` konfiguriert.
  - Nur Nachrichten dieser Nummer dürfen standardmäßig Befehle auslösen.
- **Gruppen-Chat**:
  - Typischerweise eine Gruppe wie `Haruko`.
  - Nachrichten des Masters werden ohne Prefix an Haruko weitergereicht, andere Teilnehmer nur mit Passwort.
- **Passwort für Fremdzugriff**:
  - Konstante `FOREIGN_PASSWORD` im Skript.
  - Syntax: `PASSWORT: <Befehl>` oder `PASSWORT <Befehl>`.
  - Die Bridge entfernt das Passwort und leitet nur den eigentlichen Befehl an das Backend weiter.
- **Loop-Schutz**:
  - Gesendete Bot-Nachrichten werden in einem Set (`botMessageIds`) gespeichert.
  - Eingehende Nachrichten mit bekannter ID werden ignoriert, um Selbst-Antwort-Schleifen zu verhindern.

### Start & Autostart
- Die Bridge kann gemeinsam mit Backend/Frontend über ein Startskript wie `start_haruko_windows.bat` gestartet werden (separates Konsolenfenster, QR-Code-Ausgabe).
- Optionaler Autostart über ein Windows-Startup-Skript, das dieses Startskript verlinkt.

## Roadmap & Future Improvements (Technischer Ausblick)

Hier sind geplante Verbesserungen und technische Ansätze für zukünftige Entwickler.

### 1. Offline-Fähigkeit & TTS Fallback (High Priority)
Aktuell ist das System bei Edge-TTS auf Internet angewiesen.
- **Ziel**: Automatischer Fallback auf lokale Synthese bei Netzwerkausfall.
- **Implementierungsvorschlag**:
  - Integration von **Piper TTS** (leichtgewichtig, schnell, läuft auf CPU).
  - In `tts_cli.py`: `try-except` Block um Edge-TTS. Bei `Exception` -> Aufruf von Piper Binary.
  - *Vorteil*: System spricht auch ohne Internet weiter.

### 2. HTTPS-Zwang & Sicherheit
Browser blockieren oft den Mikrofon-Zugriff auf `http://`.
- **Ziel**: Automatische Umleitung oder striktes HTTPS.
- **Implementierungsvorschlag**:
  - In `main.py` (FastAPI): Middleware `HTTPSRedirectMiddleware` aktivieren.
  - Einsatz eines Reverse Proxies (Nginx/Caddy) für SSL-Termination (statt selbst-signierter Zertifikate via Python).
  - *Vorteil*: Stabilerer Mikrofon-Zugriff auf mobilen Geräten.

### 3. Latenz-Optimierung (Audio Pipeline)
Die Kette `WebM -> WAV -> Vosk` erzeugt Latenz.
- **Ziel**: Schnellere Reaktion ("Realtime"-Gefühl).
- **Implementierungsvorschlag**:
  - Umstieg auf **Streaming-STT** (Audio-Chunks direkt via WebSocket an Vosk/Whisper senden, statt File-Upload).
  - Nutzung von **Faster-Whisper** mit Int8-Quantisierung für höhere Genauigkeit bei gleicher Geschwindigkeit.

### 4. Smart Home: Local-First
Aktuell starke Abhängigkeit von der Tuya Cloud API.
- **Ziel**: Unabhängigkeit von China-Servern und Internet.
- **Implementierungsvorschlag**:
  - Erzwingen der lokalen Steuerung in `tinytuya`.
  - Extraktion der `localKey`s aller Geräte und Speicherung in `cameras_config.json` oder neuer DB.
  - Fallback zur Cloud nur, wenn Gerät lokal nicht erreichbar.
