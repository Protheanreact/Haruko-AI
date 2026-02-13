# Haruko (MoltBot) Server Deployment Guide

Diese Anleitung beschreibt, wie du Haruko auf einem frischen Ubuntu Server (22.04 oder 24.04) installierst.

## Hardware Voraussetzungen
- **Option A (Empfohlen für Leistung):**
  - **GPU:** NVIDIA RTX 3060 (12GB) oder besser.
  - **RAM:** 32GB DDR4/DDR5.
  - **Vorteil:** Sehr schnell, läuft mit Llama 3 (8B) flüssig.

- **Option B (Stromsparend / Orange Pi 5 Plus):**
  - **Board:** Orange Pi 5 Plus (16GB RAM Version).
  - **Vorteil:** Günstig, extrem stromsparend (ca. 10 Watt).
  - **Nachteil:** Llama 3 (8B) ist hier etwas langsam (ca. 2-3 Wörter/Sekunde).
  - **Lösung:** Nutze das kleinere Modell **Llama 3.2 3B** (läuft schnell & flüssig auf diesem Board).

- **Option C (Der Preis-Leistungs-Tipp / Intel Mini-PC):**
  - **Gerät:** Mini-PC mit Intel Prozessor N100, N95 oder N5105 (z.B. Beelink, NiPoGi, ACE, Geekom).
  - **Kosten:** ca. 140€ - 180€ (oft inkl. Gehäuse, Netzteil, 16GB RAM & SSD).
  - **Vorteil:** 
    - Kommt oft direkt mit **16GB RAM** (wichtig!).
    - **x86 Architektur:** Alles läuft sofort (Windows oder Ubuntu), keine Bastelarbeit wie bei ARM/Pi.
    - Geringer Stromverbrauch (6-15 Watt).
  - **Leistung:** 
    - **N100:** Aktueller Favorit, sehr flott.
    - **N5105:** Vorgänger, etwas langsamer, aber für **Llama 3.2 3B** immer noch völlig ausreichend.
  - **Empfehlung:** Das ist die stressfreiste Lösung für einen Homeserver.

- **Option D (Der Nachhaltige / Refurbished Business PC):**
  - **Gerät:** Lenovo ThinkCentre Tiny, Dell OptiPlex Micro, HP ProDesk Mini, Fujitsu Esprimo (SFF oder Mini).
  - **Specs:** Suche nach Intel i5 (ab 6. Generation), 16GB RAM.
  - **Kosten:** Oft sehr günstig gebraucht (100€ - 150€).
  - **Vorteil:**
    - **Profi-Qualität:** Diese Dinger sind gebaut wie Panzer (sehr langlebig).
    - **Günstig:** Bestes Preis-Leistungs-Verhältnis bei der Anschaffung.
    - **Windows Pro:** Meistens schon dabei.
  - **Nachteil:** Verbraucht etwas mehr Strom als ein N100 (ca. 10-20 Watt im Leerlauf statt 6 Watt).
  - **Leistung:** Sehr gut für Haruko (Llama 3.2 3B läuft flüssig).

- **Option E (Premium / Gebraucht):**
  - **Gerät:** Mac Mini M1 (8GB oder 16GB) - gebraucht kaufen.
  - **Kosten:** ca. 300€ - 350€.
  - **Vorteil:** Extrem schnell für KI dank Apple Silicon. Läuft fast so gut wie große Server.

## Installation auf Windows (für Option C & D)

Wenn du einen Mini-PC oder Office-PC mit Windows nutzt, ist die Installation sehr einfach. Ich habe ein **All-In-One Setup** gebaut.

1.  **Ordner kopieren:** Kopiere den gesamten `moltbotback` Ordner auf den PC (z.B. nach `C:\Haruko`).
2.  **Setup starten:**
    - Öffne den Ordner.
    - Mache einen Doppelklick auf `setup_windows.bat`.
    - Bestätige evtl. die Administrator-Rechte.
    - **Das war's!** Das Skript prüft alles, installiert automatisch Python, Node.js & Ollama (falls sie fehlen) und lädt die KI herunter.
3.  **Starten:**
    - Doppelklick auf `start_haruko_windows.bat`.

---

## Installation auf Linux (Ubuntu / Orange Pi)

Folge diesen Schritten, wenn du Linux nutzt:

## Schritt 1: System vorbereiten & Treiber

1. **System aktualisieren:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git curl build-essential python3-venv python3-pip ffmpeg portaudio19-dev
   ```

2. **NVIDIA Treiber installieren (falls NVIDIA GPU):**
   ```bash
   sudo apt install -y nvidia-driver-535 nvidia-utils-535
   sudo reboot
   ```
   *Nach dem Neustart prüfen mit `nvidia-smi`.*

3. **Node.js installieren (für das Frontend):**
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
   sudo apt install -y nodejs
   ```

## Schritt 2: Ollama (KI-Engine) einrichten

1. **Installieren:**
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Modell laden:**
   Wir nutzen das moderne und effiziente **Llama 3.2**, das auf allen empfohlenen Geräten (PC, Orange Pi, Mac) super läuft.
   ```bash
   ollama pull llama3.2
   ```

3. **Testen:**
   ```bash
   ollama run llama3.2 "Hallo, bist du bereit?"
   # Mit Strg+D beenden
   ```

## Schritt 3: Haruko installieren

1. **Projektordner auf den Server kopieren** (z.B. nach `/opt/haruko` oder in dein Home-Verzeichnis).

2. **Setup-Script ausführen:**
   ```bash
   cd /pfad/zu/haruko/release/setup
   chmod +x setup_linux.sh
   ./setup_linux.sh
   ```

## Schritt 4: Als Dienst einrichten (Autostart)

Damit Haruko immer im Hintergrund läuft und nach einem Neustart automatisch startet, habe ich ein Script vorbereitet.

1. **Autostart Script ausführen:**
   ```bash
   cd ~/moltbotback/release/setup
   chmod +x setup_autostart.sh
   sudo ./setup_autostart.sh
   ```

2. **Hardware auswählen:**
   Das Script fragt dich, ob du einen **PC** oder **Orange Pi** nutzt.
   - Wähle **2** für Orange Pi (es stellt automatisch auf das schnellere Modell um).

3. **Fertig!**
   Haruko läuft jetzt. Du kannst den Status prüfen mit:
   ```bash
   sudo systemctl status haruko-backend
   ```

## Wichtiger Hinweis zum Audio

Da der Server wahrscheinlich irgendwo im Keller/Schrank steht:
- **Mikrofon:** Du nutzt das Mikrofon am Client (Handy/Laptop) über die Webseite. Das funktioniert super.
- **Lautsprecher:** Aktuell spielt das Backend den Ton über `pyttsx3` direkt am Server ab.
  - *Lösung:* Schließe Boxen an den Server an, wenn du ihn hören willst.
  - *Oder:* Wir müssen in Zukunft auf "Browser-TTS" umstellen, damit der Ton aus deinem Handy kommt (das erfordert Code-Anpassungen).

## Häufige Fragen (FAQ)

**Q: Brauche ich keine teure Grafikkarte (GPU)?**
A: Für das kleine Modell (**Llama 3.2 3B**) nicht!
- Bei großen Modellen braucht man zwingend eine NVIDIA Karte.
- Aber das 3B-Modell ist so effizient, dass der **Prozessor (CPU)** und der **Arbeitsspeicher (RAM)** die Arbeit erledigen.
- Die eingebaute Intel HD Grafikkarte im Fujitsu/Lenovo wird für die KI gar nicht genutzt (sie ist nur für den Monitoranschluss da). Das ist völlig okay so.

**Q: Warum sind 16GB RAM so wichtig?**
A: Die KI muss komplett in den schnellen Arbeitsspeicher geladen werden.
- Windows braucht ca. 4GB.
- Die KI braucht ca. 3-4GB.
- Der Rest ist "Luft zum Atmen" für flüssige Antworten.
- Mit nur 8GB würde der PC anfangen, Daten auf die langsame Festplatte auszulagern -> Haruko würde stottern oder abstürzen.
