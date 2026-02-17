# Konzept: Haruko Phygital - Die Verschmelzung von Raum und Avatar

**Status**: Entwurf / Brainstorming
**Datum**: 04.02.2026
**Autor**: Haruko AI Team

Dieses Dokument beschreibt die geplante Erweiterung von Haruko um "physische" Sinne. Ziel ist es, die Grenze zwischen dem digitalen Assistenten und dem physischen Raum aufzulösen.

---

## 1. Architektur-Upgrade: Von Cloud zu Local-First

Aktuell nutzt Haruko die `tinytuya.Cloud` API. Diese ist einfach einzurichten, hat aber Nachteile:
- **Latenz**: 1-3 Sekunden Verzögerung.
- **Limits**: Begrenzte API-Calls pro Tag.
- **Polling**: Nicht geeignet für Echtzeit-Sensoren (Temp/Motion).

### Der Plan: Hybrid-Ansatz
Wir stellen auf `tinytuya.Device` (Local Network Control) um.
1.  **Discovery**: Beim Start scannt Haruko das LAN nach Tuya-Geräten.
2.  **Local Keys**: Wir extrahieren die `localKey`s aller Geräte (einmalig via Cloud-Wizard) und speichern sie in `devices_config.json`.
3.  **Event-Loop**: Ein Hintergrund-Thread (`SensorMonitor`) pollt lokale Geräte alle 5-30 Sekunden (sehr schnell im LAN).

---

## 2. Feature: Raumklima-Feedback ("Mir ist heiß!")

**Idee**: Der Avatar reagiert auf die physische Temperatur im Raum.

### Technische Logik
1.  **Sensor**: Tuya Temperatur/Feuchtigkeitssensor (WiFi oder Zigbee).
2.  **Logik (in `main.py`)**:
    ```python
    if temp > 26.0:
        set_avatar_state("hot") # Schwitzen, Fächern, Sommerkleid
    elif temp < 18.0:
        set_avatar_state("cold") # Zittern, Schal, Wintermantel
    else:
        set_avatar_state("neutral")
    ```
3.  **Frontend (React)**:
    - Der State wird via WebSocket gepusht.
    - `VRMAvatar.tsx` lädt das entsprechende Modell oder aktiviert BlendShapes (z.B. gerötete Wangen).

### User Experience
- Wenn du fragst "Wie ist das Wetter?", antwortet sie: "Draußen 15 Grad, aber hier drinnen kuschlige 22 Grad."

---

## 3. Feature: Präsenzerkennung (Zero-Touch Greeting)

**Idee**: Begrüßung beim Betreten des Raumes, ohne "Hey Haruko" sagen zu müssen.

### Herausforderung
Tuya-Bewegungsmelder (PIR) sind oft batteriebetrieben und senden erst nach 3-5 Sekunden ein Signal an die Cloud ("Deep Sleep").

### Lösungen
*   **Option A (Tuya PIR)**: Akzeptieren der Latenz. Begrüßung kommt halt erst, wenn man schon sitzt.
*   **Option B (Webcam Vision - Empfohlen)**: 
    - Haruko nutzt die Webcam, um alle 2 Sekunden einen schnellen "Person Check" zu machen (lokales Modell, z.B. YOLO/MediaPipe, NICHT Gemini um Kosten zu sparen).
    - Wenn `Person erkannt` UND `Letzte Sichtung > 30 Min`:
        -> Trigger TTS: "Willkommen zurück, Meister."

### Spam-Schutz (Cooldown)
Wichtig: Wir brauchen eine `last_greeting_time` Variable. Sie darf nicht jedes Mal grüßen, wenn man kurz aufs Klo geht.
- **Regel**: Nur grüßen, wenn > 30 Minuten keine Präsenz erkannt wurde.

---

## 4. Feature: Ambient Sync (Licht-Verschmelzung)

**Idee**: Der Monitorhintergrund passt sich der Raumbeleuchtung an.

### Technische Umsetzung
1.  **Mapping**: Wir lesen die RGB-Werte der smarten Glühbirnen aus (Tuya DPS Indizes).
2.  **Sync**:
    - Backend sendet `{"ambient_color": "rgb(255, 100, 50)"}`.
    - Frontend (`AIBackground.tsx`) nutzt CSS Transitions:
      ```css
      .background {
          background: linear-gradient(to bottom, var(--ambient-color), #000);
          transition: background 2s ease-in-out;
      }
      ```
3.  **Effekt**: Wenn du das Licht im Raum dimmst oder rot machst, wird auch Harukos Welt dunkel/rot.

---

## 5. Nächste Schritte (Roadmap)

1.  [ ] **Hardware-Check**: Hast du passende Sensoren (Temp/Motion)?
2.  [ ] **Local Keys**: Ein Skript schreiben, das alle `localKey`s deiner Geräte exportiert.
3.  [ ] **Prototyping**:
    - Erstmal nur Temperatur auslesen und im Terminal ausgeben.
    - Dann Frontend-Anbindung.