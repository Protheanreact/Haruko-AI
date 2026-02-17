# Changelog

## [2026-02-13] - Version 2.10: The Self-Awareness Update

### ✨ Neue Features
- **Librarian (Der Bibliothekar)**:
  - Neuer Hintergrund-Dienst (`librarian.py`) für System-Integrität und Wissenspflege.
  - **Self-Correction**: Überwacht stündlich Speicherplatz, Internetverbindung und Datenbank-Integrität.
  - **Knowledge Maintenance**: Aktualisiert und erweitert bestehende Markdown-Wissensdateien im `knowledge/` Ordner basierend auf neuen Erkenntnissen.
- **Dynamic User Profiler**:
  - Haruko erstellt und aktualisiert nun dynamisch psychologische Profile ihrer Nutzer.
  - Speicherung in neuer SQLite-Tabelle `user_profiles` (JSON-Attribute).
  - **Funktionsweise**: Analysiert Gespräche auf Persönlichkeitsmerkmale, Vorlieben und Stimmungen und passt den Kontext zukünftiger Gespräche an.
  - Integration in den System-Prompt: Haruko "weiß", wer vor ihr sitzt (via FaceID) und wie dieser User tickt.

### ⚡ Verbesserungen
- **Memory DB**: Erweiterung um `user_profiles` Tabelle.
- **System-Prompt**: Injektion von User-Profil-Daten für hyper-personalisierte Antworten.

## [2026-02-12] - Version 2.9: The Animation & Setup Update

### ✨ Neue Features
- **VRM Animation System (.vrma)**:
  - Vollständige Umstellung von FBX auf das native VRM-Animationsformat (`.vrma`).
  - Behebt "Black Screen" und WebGL-Kontextverluste durch inkompatible FBX-Loader.
  - Ermöglicht flüssiges Blending von Gesichtsausdrücken (Blinken, Sprechen) während der Animationen.
- **Interactive Setup Mode**:
  - Neuer Modus zum visuellen Einrichten von Möbel-Positionen im 3D-Raum.
  - Aktivierung via **Shift+S**.
  - **Funktionen**:
    - Gizmo-Steuerung (Verschieben/Drehen) für Stuhl- und Bett-Marker.
    - **Shift+R**: Umschalten zwischen Positionieren und Rotieren.
    - **Shift+L**: Erzwingt die Schlaf-Pose (für Bett-Kalibrierung).
    - Koordinaten werden direkt in der Browser-Konsole ausgegeben.
- **Sitting as Default**:
  - Haruko sitzt nun standardmäßig auf dem Stuhl (Idle-State), statt im Raum zu stehen.
  - Wirkt natürlicher für einen Desktop-Assistenten.
- **Smart Animation Blending**:
  - Prozedurale Gesten (Winken, Nicken, Nachdenken) werden nun "über" die aktuelle Pose (Sitzen/Liegen) gelegt.
  - Kein Zurücksetzen in die T-Pose mehr bei Interaktionen.

### ⚡ Verbesserungen
- **Auto-States**:
  - **Night Mode**: Automatische Schlafenszeit (legt sich ins Bett) basierend auf der Uhrzeit.
  - **Setup Safety**: Automatische Verhaltensmuster werden pausiert, solange der Setup-Modus aktiv ist.
- **Kamera-Steuerung**:
  - Fix für OrbitControls: Freies Drehen und Zoomen wieder möglich.

## [2026-02-10] - Version 2.8: The Multilanguage Update

### ✨ Neue Features
- **Multilanguage Support (DE/EN)**:
  - Haruko spricht nun fließend Englisch!
  - Setup-Skript fragt nach der gewünschten Sprache (Deutsch oder Englisch).
  - Automatische Anpassung von Persönlichkeit (System Prompt), Stimme (TTS) und System-Antworten.
  - "Master Switch" via `.env` Datei (`LANGUAGE=EN` oder `LANGUAGE=DE`).

## [2026-02-10] - Version 2.7.1: The Maintenance Update

### ✨ Neue Features
- **Memory Maintenance**:
  - Implementierung des "Reflexions-Loops" für das Langzeitgedächtnis (LTM).
  - Tägliche automatische Konsolidierung und Bereinigung von Fakten via Gemini Pro.

### 🐛 Bugfixes
- **Chat UI**: Fix für sichtbare `EXECUTE`-Befehle im Chatverlauf (Frontend).
- **TTS Engine**: Striktes Filtern von Emojis und Sonderzeichen (kein Vorlesen von Smileys mehr).

## [2026-02-09] - Version 2.7: The Autonomy Update

### ✨ Neue Features
- **Self-Learning (Auto-Knowledge)**:
  - Neuer Befehl: "Lern mir [Thema]" (z.B. "Lern mir SciFi schreiben").
  - Haruko recherchiert autonom via Gemini, erstellt einen strukturierten Markdown-Guide und speichert ihn in `knowledge/`.
  - Automatische Re-Indizierung: Das neue Wissen steht sofort für RAG-Abfragen zur Verfügung.
- **Network Control (Wake-on-LAN)**:
  - Integration von `network_tools.py` für Low-Level Netzwerkoperationen.
  - Haruko kann nun physische PCs im Netzwerk aufwecken (Magic Packet via UDP Broadcast).
- **Erweiterte PDF-Analyse**:
  - Verbessertes Handling großer PDF-Dateien (>600 Seiten) durch intelligentes Chunking.
  - Neues Diagnose-Tool `debug_pdf.py` zur Prüfung der Lesbarkeit.

### ⚡ Verbesserungen
- **Code Refactoring**:
  - Zentralisierung der `KnowledgeBase`-Klasse in `knowledge.py` (DRY-Prinzip).
  - Bereinigung von Redundanzen in `main.py`.
- **RAG-Engine**:
  - Fix für Updates bei "Chunked Files" (mtime-Check korrigiert).
  - Bessere Erkennung von Bild-basierten PDFs (Warn-Logs).

## [2026-02-09] - Version 2.6: The Memory Update

### ✨ Neue Features
- **Auto-Memory (Selbstständiges Lernen)**:
  - Haruko analysiert nun Gespräche und speichert wichtige Fakten (z.B. Vorlieben, Namen) automatisch in ihrer Datenbank.
  - Kein expliziter Befehl mehr nötig ("Notiere das").
- **Langzeitgedächtnis 3.0 (SQLite)**:
  - Umstellung von JSON auf SQLite für robuste Datenspeicherung.
  - Automatische Migration bestehender Daten.
  - Thread-Safe Design für parallele Zugriffe.
- **RAG-Suche (Retrieval Augmented Generation)**:
  - Haruko kann nun aktiv in ihrem eigenen Gedächtnis suchen (`search_memory`), um Fragen zu beantworten, die länger zurückliegen.
- **Erweiterte LLM-Hierarchie**:
  - Kosten-Optimierung: Gemini Free -> Groq (Llama 3) -> OpenRouter -> Gemini Paid -> Ollama (Offline).
  - Maximale Verfügbarkeit durch 5-Stufen-Fallback-System.

### ⚡ Verbesserungen
- **Server Deployment**:
  - `update_server_v2.5_memory` Paket für einfache Synchronisation.
  - Verbesserte Pfad-Handhabung (`BASE_DIR`) für Cross-Platform Kompatibilität.
- **Dokumentation**:
  - Handbücher (DE/EN) auf Stand v2.6 gebracht.

## [2026-02-06] - Autonomous Avatar & Storytelling Update

### ✨ Neue Features
- **Project Lead & Design**:
  - Großes Update unter der Leitung von **Stephan Eck (Protheanreact)**.
- **Vision & FaceID**:
  - Integration von `face_recognition` zur Erkennung bekannter Personen (Master, Jenny).
  - Client-Push Architektur für Mobile Vision (`MobileVision.tsx`).
- **Telegram Bot**:
  - Volle Integration für Remote-Chat und Überwachung.
  - Befehl `/cam` sendet Live-Bilder aus der Wohnung (Webcam/Screen).
- **Sekretär & Organisation**:
  - Persistente Notizen, Timer und Wecker.
  - Langzeitgedächtnis für Fakten ("Merk dir...").
- **PC-Integration**:
  - App-Launcher (Spotify, Steam, Cyberpunk, Yi IoT).
  - Systemsteuerung (Lautstärke, Shutdown, Lock).
  - Navigation: Scrollen in Apps ("Scrolle weiter") hinzugefügt.

### ⚡ Verbesserungen
- **Installation & Setup**:
  - **One-Click Setup (Windows)**: Das Setup-Skript installiert nun automatisch C++ Runtimes (Redistributable) und Build Tools.
  - **Auto-Config**: Setup fragt API-Keys (Gemini, Tuya, Telegram) interaktiv ab und erstellt die `.env` Datei.
  - **Admin-Privilegien**: Setup fordert automatisch Admin-Rechte an, falls nötig.
  - **Linux Support**: Automatische Installation von Build-Tools (`cmake`, `build-essential`) für reibungslose Kompilierung.
- **Avatar Autonomie**: 
  - Organische Idle-Animationen (Sway, Scratch, Stretch).
  - Langeweile-Erkennung: Klopft an den Bildschirm nach 45s Inaktivität.
  - Dynamisches Mood-Switching in Stories (`[MOOD:...]`).
- **Dokumentation**: 
  - Vollständiges Update aller Handbücher (HOWTO, TECHNICAL, CHANGELOG).
  - Detaillierte Anleitung für alle Sub-Systeme.

### 🐛 Bugfixes
- **TTS Backend**: Fix für `NameError: name 're' is not defined`.
- **Regieanweisungen**: Filter für `[MOOD:...]` Tags in TTS hinzugefügt.
