# Installationsanleitung (Setup Guide)

## Systemanforderungen
- **OS**: Windows 10/11 oder Linux (Ubuntu 20.04+ empfohlen).
- **Hardware**: Mindestens 8GB RAM (16GB empfohlen für lokale KI), CUDA-fähige GPU empfohlen.
- **Software**:
  - Python 3.10 oder neuer.
  - Node.js (LTS Version).
  - Ollama (für die KI).
  - FFmpeg (für Audio-Verarbeitung, auf Linux meist via apt installierbar).

## Installation

### 1. Dateien entpacken
Entpacken Sie das Projektarchiv an einen gewünschten Ort (z.B. `C:\Haruko` oder `/opt/haruko`).

### 2. KI-Modelle einrichten

#### Lokale KI (Ollama)
Laden Sie Ollama von [ollama.com](https://ollama.com) herunter und installieren Sie es.
Starten Sie Ollama und laden Sie das Standard-Modell:
```bash
ollama pull llama3.1
```
*(Optional: `deepseek-r1:8b` für Logik-Aufgaben)*

#### Cloud KI (Gemini - Empfohlen für Autonomie)
Für die beste Performance und Funktionen wie **Memory Reflection (Gedächtnis-Pflege)** und **Self-Learning** nutzt Haruko Google Gemini.
- Besorgen Sie sich einen kostenlosen API-Key bei Google AI Studio.
- Tragen Sie diesen in `backend/main.py` oder als Umgebungsvariable ein.
- *Ohne diesen Key funktionieren die erweiterten Autonomie-Funktionen nicht.*

### 3. Setup-Skript ausführen

Das Setup-Skript ist nun vollständig automatisiert und kümmert sich um Abhängigkeiten (wie C++ Runtimes) und Konfiguration.

#### Windows
Es gibt zwei Wege unter Windows:

1. **Empfohlen (AIO-Installer im Projektroot)**  
   - Navigieren Sie in den Projektordner (dort, wo `setup_windows.bat` liegt).
   - Führen Sie aus:
     ```powershell
     .\setup_windows.bat
     ```
   - Dieses Skript ruft `install_haruko_aio.ps1` auf und installiert:
     - Python + Backend-Abhängigkeiten
     - Node.js + Frontend-Abhängigkeiten
     - Ollama + Modelle
     - Optionale Tools wie die WhatsApp-Bridge-Vorlage

2. **Erweitert (älteres Skript in release/setup)**  
   - Navigieren Sie in den Ordner `release/setup`.
   - Führen Sie aus:
     ```powershell
     .\setup_windows.ps1
     ```
   - **Sprachauswahl**: Das Skript fragt Sie nach der gewünschten Sprache (DE oder EN).
   - Das Skript fordert automatisch Admin-Rechte an, um Systemkomponenten zu installieren.
   - Es wird Sie nach Ihren API-Keys (Gemini, Tuya, Telegram) fragen und die Konfiguration erstellen.
   - *Falls Skripte deaktiviert sind: `Set-ExecutionPolicy RemoteSigned` ausführen.*

#### Linux / Ubuntu Server
1.  Navigieren Sie in den Ordner `release/setup`.
2.  Machen Sie das Skript ausführbar:
    ```bash
    chmod +x setup_linux.sh
    ```
3.  Führen Sie es aus:
    ```bash
    ./setup_linux.sh
    ```
    - Das Skript installiert automatisch notwendige Build-Tools (`cmake`, `build-essential`).

### 4. Konfiguration (Automatisiert)
Das Setup-Skript hat die meisten Einstellungen bereits vorgenommen.
- Überprüfen Sie die erstellte `backend/.env` Datei, falls Sie Änderungen vornehmen möchten.
- **Frontend IP**:
  - Öffnen Sie `frontend/.env`.
  - Ändern Sie `VITE_API_URL` zu Ihrer Server-IP (z.B. `https://192.168.1.100:8000`).

## Starten
Starten Sie Backend und Frontend (siehe How-To).
