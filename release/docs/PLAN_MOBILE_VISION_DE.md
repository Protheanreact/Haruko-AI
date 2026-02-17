# Konzept: Mobile Vision & FaceID Integration

## Ziel
Haruko soll über die Kamera eines Tablets oder Handys (das als Dashboard dient) "sehen" können.
Sie soll erkennen, wer vor ihr steht (FaceID) und entsprechend reagieren (Begrüßung vs. Alarm).

## Architektur: "Client-Push"
Da der Browser (React) keinen direkten Zugriff auf die Server-Webcam zulässt und mobile Browser RTSP blockieren, drehen wir den Spieß um:
**Das Tablet sendet aktiv Bilder an Haruko.**

1.  **Frontend (Tablet/Handy)**
    - Eine React-Komponente (`MobileVision.tsx`) greift auf die Frontkamera zu.
    - Sie macht alle X Sekunden (z.B. 5s) oder bei Bewegungserkennung einen Snapshot.
    - Dieser Snapshot wird per HTTP POST an den Server gesendet (`/api/vision/analyze`).

2.  **Backend (Server)**
    - Empfängt das Bild.
    - Nutzt `face_recognition` Library (dlib) für Gesichtserkennung.
    - Vergleicht das Gesicht mit Bildern im Ordner `known_faces/`.

3.  **Reaktion**
    - **Master erkannt**: Haruko sagt "Willkommen zurück, Master!" (Cooldown: 10 Min).
    - **Unbekannt**: Haruko loggt das Event, sendet ggf. ein Telegram-Bild ("Unbekannte Person im Wohnzimmer!").
    - **Leer**: Nichts passiert.

## Installation & Setup
1.  **Requirements**: `pip install face_recognition` (benötigt C++ Build Tools für dlib).
2.  **Known Faces**: Lege Bilder von bekannten Personen in `backend/known_faces/` ab (z.B. `master.jpg`).
3.  **Aktivierung**: Im Frontend unter Einstellungen "Mobile Vision (FaceID)" aktivieren.

## Troubleshooting: FaceID / dlib Fehler
Falls `pip install face_recognition` mit "Failed building wheel for dlib" fehlschlägt (typisch auf Windows):

**Option A (Schneller Fix):**
1.  `pip install cmake`
2.  `pip install --upgrade setuptools`
3.  `pip install dlib` (erneut versuchen)

**Option B (Offizieller Weg):**
1.  Installiere [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
2.  Wähle beim Installieren **"Desktopentwicklung mit C++"** aus.
3.  Danach `pip install face_recognition` wiederholen.

**Fallback Modus:**
Falls FaceID nicht installiert werden kann, nutzt Haruko automatisch **OpenCV** als Fallback.
- Sie erkennt, *dass* eine Person da ist ("Unbekannt").
- Sie kann aber *nicht* unterscheiden, wer es ist.

## Status
- [x] Backend Dependencies (`face_recognition`)
- [x] Backend Logic (`vision.py`, `analyze_faces`)
- [x] API Endpoint (`/api/vision/analyze`)
- [x] Frontend Component (`MobileVision.tsx`)
- [x] Frontend Integration (`App.tsx`)
