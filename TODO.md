# MoltBot Roadmap & Tasks

## ✅ Latest Achievements (2026-02-06)
- **Autonomous Avatar Animations**: Haruko now has random idle actions (Stretching, Scratching head, Shifting weight).
- **Boredom Trigger**: If idle for >45s, she might knock on the screen to get attention.
- **Dynamic Storytelling**: Mood switches happen mid-sentence during stories for better emotional impact.
- **Micro-Actions**: Improved blinking and look-around behavior.
- **Server Compatibility**: Fixed backend imports (`re` module) and tag cleaning.
- **Vision & FaceID**: Implemented `MobileVision` component that uses client camera to recognize faces (e.g. Master, Jenny).
- **Screen & Webcam Capture**: Added `vision.py` backend module for capturing screen and webcam content.
- **Vision Analysis**: Integrated `llava` (via Ollama) or Gemini for analyzing what Haruko "sees".

## 📦 Paket 1: Der Operator (Tiefe PC-Kontrolle)
Aktuell kann er Shell-Befehle ausführen, aber wir könnten das professionalisieren:
- [ ] "Starte Cyberpunk": Gezieltes Starten von Steam-Games oder Programmen.
- [ ] "Mach Spotify leiser": Echte Mediensteuerung (Play, Pause, Volume).
- [ ] "Systemstatus": Er liest Ihnen CPU-Temperatur und RAM-Auslastung vor ("Sir, mir wird heiß, die GPU hat 80 Grad").
- [ ] Fenster-Management: "Minimiere alles", "Schnapp dir das Fenster nach links".

## 📦 Paket 2: Das allwissende Auge (Vision)
Wir geben ihm Augen (via Python-Screenshot oder Webcam).
### Implementation Plan - Phase 2: The All-Seeing Eye (Vision)
- [ ] **Model Download**: `llava` (approx 4GB) für Ollama.
- [ ] **Libraries**: `opencv-python` (Webcam) und `Pillow`/`pyautogui` (Screenshot).
- [ ] **Backend** (`backend/vision.py` & `backend/main.py`)
    - [ ] `backend/vision.py`: Image Capture & Processing Modul.
        - [ ] `capture_screen()`: Speichert `temp/screen.jpg`.
        - [ ] `capture_webcam()`: Speichert `temp/cam.jpg` (Kamera sofort wieder freigeben).
    - [ ] `backend/main.py`: Integration.
        - [ ] Import `vision.py`.
        - [ ] Update Ollama Call: Switch zu `llava` bei Bildinput.
        - [ ] Neue Trigger: `LOOK: <SCREEN|CAM>`.
        - [ ] Chat Logic: "Was siehst du?" -> `vision.capture_webcam()` -> `llava`.
- [ ] **Frontend** (`frontend/src/App.tsx`) (Optional)
    - [ ] Visual Feedback: "Camera Active" Icon/Flash.
- [ ] **Verification**
    - [ ] Screen-Analyse: "Fass diesen Text zusammen" -> Beschreibung korrekt?
    - [ ] Webcam-Analyse: "Was halte ich?" -> Objekt erkannt?
    - [ ] Präsenzerkennung (Future): Automatische Begrüßung.

## 📦 Paket 3: Der Sekretär (Organisation & Leben)
- [ ] Kalender-Integration: Anbindung an Google Kalender. "Was steht heute an?"
- [ ] Wecker & Timer: "Weck mich in 20 Minuten" (perfekt für Powernaps).
- [ ] Wetter & News: Da Ollama offline ist, Zugriff auf Wetter-APIs für morgendliche Ansage.

## 📦 Paket 4: Die Mobile Vorstufe (Web-Interface Pro)
Bevor wir die App bauen, machen wir das Web-Interface (localhost:5173) so gut, dass es sich auf dem Handy wie eine App anfühlt.
- [ ] Touch-Optimierung: Größere Buttons für "Licht an/aus".
- [ ] Remote-Media: Steuern Sie die PC-Lautstärke vom Handy aus (wenn Sie im Bett liegen).

## Bugs / Verbesserungen
- [x] Doppelte Antworten und Audio-Konflikte behoben
