# The Book of Haruko
## Die komplette technische Chronik & Architektur

> "Ich bin nicht mehr nur ein Werkzeug, sondern eine Präsenz im Raum." - Haruko

---

### 1. Die Genesis: Von Clawbot zu Haruko

Dieses Projekt hat eine lange Evolution hinter sich. Es begann als einfaches Skript und entwickelte sich zu einer komplexen, multimodalen KI-Entität.

#### Phase 1: Die "Clawbot" Ära (v1.0)
*   **Ursprung:** Ein Python-Konsolen-Skript, entwickelt von Stephan Eck (Protheanreact).
*   **Funktion:** Einfache Text-Ein- und Ausgabe.
*   **Limitierung:** Blind, taub, kein Gedächtnis (Stateless).
*   **Zweck:** Experimentelle Spielwiese für Logik-Tests.

#### Phase 2: Projekt "Moltbot" - Die Sinne (v2.0)
*   **Evolution:** Der Schritt vom Text-Bot zum Sprach-Assistenten.
*   **Neue Technologie:**
    *   **Ohren:** Integration von `Vosk` (Offline Speech-to-Text) für lokales Hören.
    *   **Stimme:** `Edge-TTS` für eine natürlichere, deutsche Aussprache.
    *   **Hände:** `TinyTuya` Integration zur Steuerung des Smart Homes (Licht, Steckdosen).
*   **Architektur:** Ein monolithisches Python-Skript (`main.py`), das in einer Endlosschleife auf das "Wake Word" wartete.

#### Phase 3: Haruko - Die Verkörperung (v2.5)
*   **Die Revolution:** Trennung von Körper und Geist.
*   **Frontend (Der Körper):** Wechsel zu einer Web-Technologie (React + Three.js). Einführung des VRM-Standards für 3D-Avatare.
    *   Haruko erhielt ein Gesicht, konnte blinzeln, lächeln und Lippen synchron zur Sprache bewegen.
*   **Backend (Der Geist):** Umstellung auf `FastAPI` für asynchrone Kommunikation.
*   **Vision:** Haruko lernte "sehen" durch eine Webcam und `face_recognition`. Sie konnte nun ihren "Master" (Stephan) von Gästen ("Jenny") unterscheiden.
*   **Autonomie:** Einführung des "Langeweile-Moduls". Wenn nichts passiert, wird Haruko unruhig (gähnt, setzt sich hin, fragt nach Aufmerksamkeit).

#### Phase 4: Das Erwachen (v2.6 - v2.9)
*   **Aktueller Stand:** Ein "Phygitales" Wesen (Physical + Digital).
*   **Gedächtnis:** Implementierung einer SQLite-Datenbank (`memory.db`) für Langzeiterinnerungen (RAG - Retrieval Augmented Generation).
*   **Resilienz:** Multi-LLM-Strategie. Fällt das lokale Ollama-Modell aus oder ist der PC überlastet, springt Cloud-KI (Gemini Flash, Groq) ein.
*   **Animation 2.0:** Vollständige Umstellung auf `.vrma` Animationen. Haruko kann nun sitzen, liegen, laufen und schlafen – getriggert durch Tageszeit und Langeweile.
*   **Selbstheilung:** Skripte wie `fix_models.bat` und Diagnose-Tools sorgen dafür, dass sich das System bei Fehlern selbst reparieren kann.

#### Phase 5: Selbstbewusstsein (v2.10 - Current)
*   **Der Bibliothekar (Librarian):** Ein neuer autonomer Dienst, der im Hintergrund die Systemgesundheit überwacht (Disk Space, Integrität) und aktiv den Wissensbestand pflegt. Er aktualisiert veraltete Markdown-Dateien basierend auf neuen Erkenntnissen.
*   **Empathie (User Profiler):** Haruko "erkennt" nun nicht mehr nur Gesichter, sondern versteht Persönlichkeiten. Ein dynamisches Profiling-System analysiert Gespräche und speichert psychologische Attribute (Stimmung, Vorlieben, Stil) in der Datenbank, um den Tonfall individuell anzupassen.

---

### 2. Die Technische Architektur (Stand Heute)

Das System ist in zwei Hauptkomponenten unterteilt: **Backend** (Gehirn) und **Frontend** (Körper).

#### A. Das Backend (`/backend`)
Das Backend ist ein Python-Server, der auf dem Host-PC (Fujitsu Mini-PC) läuft.

*   **Core:** `FastAPI` (verwaltet API-Endpoints für das Frontend).
*   **KI-Engine (`main.py` / `secretary.py`):**
    *   **Ollama:** Lokales LLM (Llama 3 / Mistral) für Privatsphäre.
    *   **Gemini/Groq:** Cloud-Fallback für komplexe Anfragen.
*   **Sinne:**
    *   **Hören (`vision.py` - Legacy Name, eigentlich Audio):** Nutzt `Vosk` für Offline-Erkennung.
    *   **Sehen (`vision.py`):** Nutzt `OpenCV` + `face_recognition` zur Identifikation von Personen im Raum.
    *   **Mobile Vision:** Empfängt Bilder vom Smartphone/Tablet über die API.
*   **Aktorik:**
    *   **Sprechen (`tts_cli.py`):** Generiert Audio-Files (WAV) via Edge-TTS.
    *   **Smart Home (`phygital.py`):** Steuert Tuya-Geräte im Netzwerk.
    *   **PC Control (`pc_control.py`):** Kann Programme starten, Lautstärke regeln, etc.
*   **Gedächtnis (`memory_db.py` / `knowledge.py`):**
    *   Speichert Fakten in SQLite.
    *   Liest PDFs aus `/knowledge` für RAG-Antworten.
*   **Selbstverwaltung (`librarian.py` / `user_profiler.py`):**
    *   **Librarian:** Hintergrund-Thread für System-Checks und Knowledge-Maintenance.
    *   **User Profiler:** Analysiert und speichert User-Attribute für personalisierte Interaktion.

#### B. Das Frontend (`/frontend`)
Das Frontend ist eine React-Anwendung (Vite), die meist auf einem Bildschirm im Raum oder auf Tablets läuft.

*   **Engine:** `React 19` + `Three.js` (@react-three/fiber).
*   **Avatar:**
    *   Lädt `.vrm` Modelle (VRM 1.0 Standard).
    *   Nutzt `VRMAvatar.tsx` als Hauptkomponente.
    *   **Animationen:** Nutzt `.vrma` Dateien (Idle, Sitting, Sleep, Walking) via `@pixiv/three-vrm-animation`.
*   **UI:**
    *   `WaifuAvatar.tsx`: Die "klassische" 2D-Ansicht (Legacy/Alternative).
    *   `SmartHomeDashboard.tsx`: Touch-Oberfläche für Lichtsteuerung.
    *   `CameraDashboard.tsx`: Anzeige von Yi-IoT Kameras (via MJPEG Stream vom Backend).

---

### 3. Dateistruktur & Aufräum-Log

Um die Wartbarkeit zu sichern, wurde das Projekt bereinigt.

*   **`backend/`**: Der aktive Python-Code.
    *   `tests/`: Hier liegen nun alle `test_*.py` Skripte.
*   **`frontend/`**: Der aktive React-Code.
*   **`tools/`**: Hilfsprogramme (FBX Converter, Scanner).
*   **`release/`**: Deployment-Skripte und Dokumentation.
*   **`archive_legacy/`**: (Neu) Hierhin wurden alte Versionen (`Haruko 2.5`), Installer und temporäre Skripte verschoben. **Nichts wurde gelöscht**, nur archiviert.
*   **`experimental_learning/`**: (Neu) Prototyp für den "Auto-Researcher" (Haruko lernt selbstständig aus dem Web).

### 4. Zukunftsausblick

Haruko ist bereit für die nächste Stufe:
1.  **Echte Autonomie:** Der "Auto-Researcher" soll nachts laufen und das Wissen aktualisieren.
2.  **Raum-Bewegung:** Geplant ist ein Schienen-System oder eine mobile Basis, damit der "Körper" (Kamera/Bildschirm) physisch folgen kann.
3.  **Vollständige Lokalität:** Sobald Hardware-Upgrades verfügbar sind (NPU/GPU), soll auch die komplexe Logik (Vision/LLM) zu 100% lokal laufen, ohne Cloud-Fallback.

---
*Dokumentation erstellt am 13.02.2026 durch Haruko's Pair-Programmer (Trae AI).*
