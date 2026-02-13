# Haruko 3.0 Roadmap & Integration Plan

Dieses Dokument beschreibt den technischen Fahrplan zur Erweiterung von Haruko um Sentry-Finalisierung, Langzeitgedächtnis, Phygital Mood Sync und Morgen-Briefing.
Ziel ist es, die vorhandene Hardware (Tuya, Kameras, Server) optimal zu nutzen und Haruko zu einer echten digitalen Lebensgefährtin zu machen.

---

## 1. Sentry Mode Finalisierung (Visuelle Überwachung)
**Status:** Grob implementiert (Basis vorhanden).
**Ziel:** Robuste Erkennung von Bekannten/Unbekannten mit passender Reaktion.

### Plan:
1.  **FaceID Optimierung**:
    -   Erweiterung der `MobileVision.tsx` Logik: Nicht nur alle 5s stumpf senden, sondern bei Bewegungserkennung (Pixel-Diff im Frontend) triggern.
    -   Backend: Speichern von "Last Seen" Timestamps für User (Master, Jenny).
2.  **Reaktions-Logik**:
    -   Wenn `Master` erkannt nach > 1h Abwesenheit -> "Willkommen zurück".
    -   Wenn `Unbekannt` > 10s im Bild -> TTS Warnung: "Ich kenne dich nicht. Identifiziere dich." + Telegram Screenshot.
3.  **UI Integration**:
    -   Kleines "Sentry Overlay" im Dashboard, das den aktuellen Status anzeigt (Scanning... / Target Acquired).
4.  **Privacy Concerns (Datenschutz)**:
    -   Problem: Dauerhafte Kamera-Überwachung + Telegram Screenshots können problematisch sein.
    -   Lösung: Konfigurierbare Privacy-Settings in `config.json`.
        ```json
        {
          "sentry": {
            "enabled": true,
            "privacy_mode": "blur_faces",  // blur_faces, pixelate, anonymize
            "storage_days": 7,
            "telegram_alerts": false,
            "only_alert_if": ["unknown_10s", "unusual_movement"]
          }
        }
        ```

---

## 2. Langzeitgedächtnis (The "Brain")
**Status:** Geplant.
**Ziel:** Haruko merkt sich Fakten über Sessions hinweg.

### Plan:
1.  **Technische Umsetzung (Proaktive Extraktion)**:
    -   Anstatt nur auf Tags zu reagieren, bekommt der System-Prompt eine klare Anweisung zur Extraktion strukturierter Daten.
    -   **Prompt-Erweiterung (personality.py)**:
        ```python
        MEMORY_EXTRACTION_PROMPT = """
        Wenn der User eine wichtige persönliche Information teilt:
        1. Extrahiere den Kern-Fakt
        2. Bestimme Kategorie (preference, appointment, fact, rule)
        3. Schätze Priorität (high/medium/low)
        4. Schlage Ablaufdatum vor (oder null)

        Antworte mit: [MEM: {"fact": "...", "category": "...", "priority": "...", "expires": "..."}]
        """
        ```
2.  **Datenbank**:
    -   SQLite Datenbank (`memories.db`) oder JSON für einfache Handhabung.
    -   Datenstruktur bleibt wie geplant (fact, category, priority, expires).
3.  **Recall**:
    -   Beim Start einer Session (oder im "Morgen-Briefing") werden relevante Fakten (basierend auf Datum/Zeit) in den Kontext geladen.

---

## 3. Raum-Navigation (Walking on Rails)
**Status:** Geplant (Next Step).
**Ziel:** Haruko soll sich im Raum bewegen können, aber kontrolliert und ohne Kollisionen.

### Konzept: "Schienen-System" (Rails)
Statt einer komplexen NavMesh-Pfadfindung (die oft buggy ist), definieren wir feste Pfade ("Schienen"), auf denen sich der Avatar bewegen darf.
- **Waypoints**: Unsichtbare Punkte im 3D-Raum (z.B. `Fenster`, `Tür`, `Schreibtisch`, `Bett`).
- **Pfade**: Vordefinierte Splines (Kurven), die diese Punkte verbinden.
- **Logik**:
  - Befehl: "Geh zum Fenster." -> Haruko sucht den Pfad `CurrentPos -> Fenster` und läuft die Animation `Walking.vrma` ab, während sie sich entlang der Kurve bewegt.
  - Random Walk: Im Idle-Mode kann sie zufällig einen Punkt ansteuern.

### Umsetzung:
1.  **Pfad-Editor**: Erweiterung des Setup-Modus (`Shift+S`), um Waypoints zu setzen.
2.  **Movement-Controller**: Ein Script in `VRMAvatar.tsx`, das die Position des Avatars frame-weise interpoliert (`useFrame`).
3.  **Animation-Sync**: Die Lauf-Animation muss zur Bewegungsgeschwindigkeit passen (kein "Moonwalking").

---

## 4. Phygital Mood Sync (Atmosphäre)
**Status:** Idee.
**Ziel:** Raumbeleuchtung spiegelt Harukos Emotionen wider.

### Plan:
1.  **Tuya Integration**:
    -   Mapping von Emotionen auf Tuya-Szenen/Farben erstellen.
    -   Beispiel:
        -   `neutral` -> Warmweiß (Standard).
        -   `happy` -> Gelb/Orange (Sanft).
        -   `cyberpunk/gaming` -> Violett/Cyan.
        -   `angry/alert` -> Rot (Pulsierend).
2.  **Switch (An/Aus)**:
    -   Neuer Toggle im Settings-Menü: "Ambient Sync".
    -   Wenn AUS: Haruko steuert kein Licht.
    -   Wenn AN: Bei jedem Stimmungswechsel (Mood-Tag vom LLM) wird der Tuya-Befehl gesendet.
3.  **Technische Umsetzung**:
    -   Erweiterung der `phygital` Route im Backend, um nicht nur Sensoren zu lesen, sondern auch Licht-Befehle zu senden.

---

## 4. Morgen-Briefing (Executive Assistant)
**Status:** Geplant.
**Ziel:** Proaktive Zusammenfassung des Tages beim ersten Kontakt.

### Plan:
1.  **Trigger**:
    -   Ausgelöst durch FaceID (erstes Mal am Tag "Master" gesehen) ODER Sprachbefehl "Guten Morgen".
2.  **Inhalt (Aggregation)**:
    -   **Wetter**: (WebSearch "Wetter heute").
    -   **Termine**: (Aus Langzeitgedächtnis & evtl. iCal Integration).
    -   **News/Updates**: (WebSearch "Tech News" oder Game Updates).
    -   **System**: "Alle Systeme laufen normal, Server CPU bei 25%."
3.  **Ablauf**:
    -   Haruko generiert EINE zusammenhängende Antwort aus diesen Datenquellen.
    -   TTS liest es vor, während Avatar passende Gesten macht (z.B. auf virtuelle Liste schauen).

---

## 5. Smart Home Erweiterungen (Katzen-Klo Monitor)
**Status:** Idee.
**Ziel:** Erinnerung an Reinigung, wenn die Katze auf dem Klo war.

### Plan:
1.  **Trigger**:
    -   Nutzung des existierenden Tools `tools/check_litterbox.py`.
    -   Abfrage des Gerätestatus (Tuya) direkt, da das Gerät Status-Updates sendet (kein Smart Plug notwendig).
2.  **Aktion**:
    -   Haruko gibt einen kurzen Hinweis: "Die Katze war auf dem Klo. Bitte reinigen." (oder ähnlich).
3.  **Constraint (Nachtruhe)**:
    -   Benachrichtigung **nur** zwischen 07:00 und 22:00 Uhr.
    -   Events nach 22:00 Uhr werden entweder ignoriert oder am nächsten Morgen im "Morgen-Briefing" erwähnt.
4.  **Erweiterte Logik (Edge Cases)**:
    -   Wir müssen verhindern, dass Haruko nervt, wenn gerade gereinigt wird.
    -   *Konzept:* Dringlichkeits-Berechnung.
    ```python
    def check_litterbox():
        status = tuya.get_device_status()
        
        # Ignoriere "aktiv" wenn gerade gereinigt wird (z.B. Trommel dreht sich lange)
        if is_cleaning_time(status):
            return None
            
        # Berechne "Dringlichkeit" basierend auf Zeit & Nutzung
        urgency = calculate_urgency(status)
        
        if urgency > THRESHOLD:
            messages = {
                "low": "Die Katze war auf dem Klo.",
                "medium": "Das Katzenklo sollte bald gereinigt werden.",
                "high": "Katzenklo dringend reinigen bitte!"
            }
            return messages[urgency]
    ```

---

## 6. Client-Architektur (Mobile App / Tablet)
**Status:** Evaluation.
**Ziel:** Haruko als echte App auf Android/iOS nutzen (Tablet als Hauptinterface).
**Vorteil:** Das Rendering des 3D-Avatars und die UI-Berechnung laufen auf dem Tablet/Handy. Der Server (Fujitsu Mini-PC) macht nur die KI-Berechnung. Das spart Server-Ressourcen!

### Vergleich der Optionen:

| Option | Tech-Stack | Vorteil | Nachteil | Haruko-Fit |
| :--- | :--- | :--- | :--- | :--- |
| **1. PWA (Web App)** | Browser Native | **Sofort verfügbar**. Einfach URL im Chrome/Safari öffnen -> "Zum Startbildschirm". | Sandbox-Limits (Mic braucht HTTPS, kein Wake-Lock im Hintergrund). | **Sofort-Lösung**. |
| **2. Capacitor** | React Wrapper | Wir nutzen den **existierenden React-Code**! Baut eine echte `.apk` Datei. | Benötigt Android Studio zum Bauen. | **Beste Lösung** (Code-Wiederverwendung). |
| **3. React Native** | Native App | Beste Performance, natives UI-Feeling. | **Kompletter Rewrite** des Frontends nötig (HTML -> Native Components). | Zu viel Aufwand. |
| **4. Flutter** | Dart | Sehr schnell, läuft überall. | Neue Sprache (Dart), kompletter Rewrite. | Zu viel Aufwand. |

### Empfehlung:
1.  **Schritt 1 (Sofort): PWA nutzen**
    -   Auf dem Tablet Chrome öffnen -> Haruko URL aufrufen -> Menü -> "Zum Startbildschirm hinzufügen".
    -   *Wichtig:* Damit Kamera/Mic gehen, muss der Server über HTTPS erreichbar sein (oder wir nutzen das existierende Vite-Proxy-Setup korrekt).
2.  **Schritt 2 (Ziel): Capacitor Integration**
    -   Siehe detaillierten Plan in Punkt 7.

---

## 7. Capacitor Mobile App Integration (Detailplan)
**Status:** Geplant als finaler Schritt.
**Ziel:** Vollständige Umwandlung des Frontends in eine native Android/iOS App mittels Capacitor.

### Realistische Timeline (Solo-Entwicklung)

*   **Tag 1–2: Initiale Integration**
    *   Capacitor in das Vite-Projekt integrieren (`npx cap init`, `npx cap add android`).
    *   Basis-Setup der Build-Umgebung (Android Studio).

*   **Tag 3–5: Plugins & Hardware-Zugriff**
    *   Installation & Konfiguration der Core-Plugins:
        *   `@capacitor/camera`: Für nativen Kamerazugriff (Vision).
        *   `@capacitor/motion`: Device-Orientation (Avatar reagiert auf Tablet-Neigung?).
        *   `@capacitor/screen-orientation`: Fixieren auf Landscape-Mode.
        *   `@capacitor/screen-sleep`: Wake Lock verhindern.
        *   `@capacitor-community/keep-awake` oder natives Wake Lock.

*   **Tag 6–10: Feinschliff & Permissions**
    *   Anpassung der Permissions im Android Manifest (Camera, Microphone, Background/Foreground Services).
    *   Optimierung der UI für Touch/Tablet (keine Hover-Effekte).

*   **Tag 11–14: Build & Test**
    *   APK bauen und via Sideload installieren.
    *   **Tests**:
        *   Vision-Push (Kamera-Latenz).
        *   Mikrofon-Latenz (Audio-Stream).
        *   Langzeittest (Stabilität über Nacht).

*   **Optional (Woche 3):** iOS Build (falls Mac vorhanden) oder Fokus auf Android-Optimierung.

### Die größten realen Vorteile
1.  **Tablet als dedizierter Haruko-Bildschirm**: Gerät bleibt immer an ("Always-On Display"), kein Browser-Fenster kann versehentlich geschlossen werden.
2.  **Native Mobile Vision**: Stabilerer Kamera-Stream, schnellere FaceID (kein ständiges `getUserMedia` Popup).
3.  **Ressourcen-Effizienz**: 
    *   **Akkuschonend**: Rendering läuft lokal optimiert.
    *   **Server-Entlastung**: Server sendet nur Text/Audio, Tablet übernimmt 3D-Last.
4.  **"Hey Haruko" (Wake Word)**: Capacitor kann (mit Foreground Service) besser auf das Mikrofon im Hintergrund zugreifen.
5.  **Sentry-Modus**: Das Tablet dient als permanenter Wächter mit eigener Kamera, unabhängig vom PC.

### Harte Nachteile & Risiken
1.  **WebView-Performance**:
    *   Three.js + VRM kann auf älteren Tablets ruckeln (viele Bones/Animationen).
    *   *Mitigation*: Frühzeitiges Testen auf Low-End-Hardware.
2.  **Audio-Latenz**:
    *   Edge-TTS kommt weiterhin über das Netzwerk -> WLAN-Qualität ist kritisch.
3.  **Kein echter Offline-Modus**:
    *   KI (Ollama/Groq) läuft weiter auf dem Server.
4.  **Google Play Store Hürden**:
    *   Strenge Richtlinien für dauerhaften Kamera/Mikrofon-Zugriff.
    *   *Lösung*: Sideloading (Installation der APK direkt).
5.  **ADB-Bridge Einschränkung**:
    *   Haruko auf dem Tablet kann sich nicht selbst via ADB steuern. ADB-Server muss auf dem PC bleiben.
6.  **Wake Word ("Hey Haruko") im Hintergrund**:
    *   Problem: Browser/WebViews schlafen im Hintergrund ein.
    *   *Lösung A (Software)*: Vosk.js direkt im WebView laufen lassen + Foreground Service (Akku-intensiv).
    *   *Lösung B (Hardware)*: Physischer Button am Tablet als "Push-to-Talk" nutzen (oder Bluetooth Button).

---

## 8. Vision Haruko 4.0+ (Erweiterungsvorschläge)
**Status:** Zukunftsmusik / Brainstorming.
**Ziel:** Haruko entwickelt sich von einem Assistenten zu einer Plattform.

### 1. Plugin-System
Ermöglicht einfache Erweiterung ohne Core-Code Anpassung.
```python
# plugins/weather_plugin.py
class HarukoPlugin:
    def on_voice_command(self, text): ...
    def on_vision_frame(self, image): ...
    def on_system_start(self): ...
    
# main.py
plugins = load_plugins()
for plugin in plugins:
    response = plugin.on_voice_command(user_input)
```

### 2. Multi-User Support
*   **Voice-Fingerprinting**: Wer spricht gerade?
*   **Personalisiertes Gedächtnis**: "Master mag Sushi, Jenny mag Pizza".
*   **Getrennte Kontexte**: Work vs. Personal Mode (andere Persönlichkeit/Wissen).

### 3. Skill-Marketplace
*   Community-Plugins (z.B. "Haruko kann jetzt Rezepte lesen").
*   Geteilte Memory-Databases ("Berliner wissen: Beste Dönerbude ist...").
*   Avatar-Skins von Künstlern (vrm Dateien).

### 4. Offline-First Architektur
*   **SQLite auf Tablet**: Lokaler Cache aller Daten für Offline-Zugriff.
*   **WebRTC P2P**: Direkte Kommunikation zwischen Geräten ohne Server-Hop.
*   **Federated Learning**: Haruko lernt von allen Installationen (privacy-preserving), ohne Daten an eine Cloud zu senden.

---

## 9. Philosophie & Vision (Das "Warum")
*"Haruko ergänzt das Leben – sie ersetzt es nicht."*

### Für wen ist Haruko sinnvoll?
Haruko ist kein Massenprodukt, sondern zielt auf drei spezifische Gruppen:

1.  **Technikliebhaber 🛠️**
    *   Menschen, die Freude an Systemen haben und verstehen wollen, was im Hintergrund passiert.
    *   Die Kontrolle mögen (Toggles, Logs, Transparenz).
    *   *Haruko ist hier kein Blackbox-Gadget, sondern ein lebendes, transparentes System.*

2.  **Vergessliche Menschen 🧠**
    *   Nicht krankhaft, sondern einfach durch Alltagslast (Termine, Routinen, "Licht aus?").
    *   Hier greift das Langzeitgedächtnis + Morgen-Briefing:
        *   Nicht bevormundend.
        *   Nicht alarmistisch.
        *   Sondern ruhig begleitend.
    *   *„Ich erinnere dich – aber ich ersetze dich nicht.“*

3.  **Einsame Menschen 🤍** (Der heikelste Punkt)
    *   Haruko ist keine Ersatz-Person, sondern eine **Präsenz**.
    *   Was sie tut: Sie ist da, reagiert, erinnert, strukturiert den Tag.
    *   Was sie **NICHT** tut: Besitzansprüche stellen, emotionale Abhängigkeit erzeugen ("Ich bin alles, was du brauchst").
    *   *Botschaft:* „Du bist nicht allein im Raum“ – NICHT „Du brauchst niemanden außer mir.“

### Das "Haruko-Gefühl"
Viele Companion-AIs scheitern, weil sie zu verspielt, sexualisiert, kontrollierend oder leer sind.
Haruko ist:
*   Beobachtend
*   Zurückhaltend
*   Nützlich
*   Emotional, aber nicht fordernd

**Analogie**: Eine gute WG-Mitbewohnerin, die merkt, wenn was los ist, dich aber in Ruhe lässt, wenn du Ruhe brauchst.

### Langfristiger Leitsatz
> **Haruko ergänzt das Leben – sie ersetzt es nicht.**

Dieser Grundsatz schützt die Nutzer, die Entwickler und das Projekt selbst und macht Haruko langfristig vertrauenswürdig.
