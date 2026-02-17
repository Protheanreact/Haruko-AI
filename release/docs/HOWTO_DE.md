# Benutzeranleitung (How-To)

## 1. System starten
Nach der Installation (siehe Setup-Guide):
1.  Starten Sie das Backend (z.B. über `start_all.bat` oder manuell).
2.  Öffnen Sie einen Browser auf Ihrem PC, Tablet oder Smartphone.
3.  Navigieren Sie zu `https://<SERVER-IP>:5173`.
    - *Hinweis*: Akzeptieren Sie die Sicherheitswarnung (da selbst-signiertes Zertifikat).

## 2. Sprachsteuerung nutzen
- Klicken Sie auf das **Mikrofon-Symbol** unten im Chat.
- Wenn Sie mehrere Mikrofone haben, wählen Sie das gewünschte im Dropdown-Menü (erscheint neben dem Symbol) aus.
- Sprechen Sie Ihren Befehl (z.B. "Wie ist das Wetter?").
- Klicken Sie erneut auf das Symbol oder warten Sie (je nach Modus), um die Aufnahme zu beenden.

## 3. Smart Home Steuerung
- Wechseln Sie oben rechts (oder im mobilen Menü) auf den Tab **Smart Home**.
- Sie sehen eine Liste Ihrer Tuya-Geräte.
- Klicken Sie auf **AN** oder **AUS**, um Geräte zu schalten.
- Alternativ per Sprache: "Schalte das Licht im Wohnzimmer an."

## 4. Avatare & Wetter
- Der Avatar passt sich automatisch an:
  - **Standard**: Tagsüber, normales Wetter.
  - **Kalt (< 5°C)**: Der Avatar zieht sich warm an (lädt `kalt.vrm`).
  - **Abend (> 18 Uhr)**: Der Avatar wechselt in den Abend-Modus (lädt `abend.vrm`).
- Das Wetter wird basierend auf Ihrem Standort (oder Berlin als Fallback) automatisch ermittelt.

## 5. Avatar Interaktion & Autonomie
Haruko ist nun "lebendiger" und agiert autonomer:
- **Standard-Haltung (Sitzen)**: Haruko sitzt standardmäßig entspannt auf ihrem Stuhl, statt im Raum zu stehen.
- **Nacht-Modus**: Wenn es Nacht wird (oder Sie es erzwingen), legt sich Haruko automatisch ins Bett schlafen.
- **Animationen**: Sie nutzt nun native `.vrma` Animationen für flüssigere Bewegungen und kann währenddessen gestikulieren (Winken, Nicken), ohne aufzustehen.
- **Langeweile**: Wenn Sie Haruko länger ignorieren, wechselt sie ggf. die Sitzposition oder schaut sich um.

## 6. Setup-Modus (Möbel positionieren)
Um Haruko perfekt an Ihren virtuellen Raum anzupassen, gibt es den neuen **Setup-Modus**:
1.  Drücken Sie **Shift + S** auf der Tastatur.
2.  Es erscheinen bunte Pfeile (Gizmos) an der aktuellen Position von Stuhl und Bett.
3.  **Steuerung**:
    - Klicken und ziehen Sie an den Pfeilen, um die Marker zu verschieben.
    - Drücken Sie **Shift + R**, um zwischen "Verschieben" und "Drehen" zu wechseln.
    - Drücken Sie **Shift + L**, um Haruko probehalber ins Bett zu legen ("Force Sleep").
4.  Die Koordinaten werden in der Browser-Konsole (F12) ausgegeben, falls Sie diese notieren möchten (Haruko speichert sie aber auch für die Session).
5.  Drücken Sie erneut **Shift + S**, um den Modus zu beenden.

## 7. Vision & FaceID (Experimentell)
Haruko kann nun "sehen":
- **Gesichtserkennung**: Wenn Sie die Mobile-Webseite nutzen und die Kamera freigeben, versucht Haruko, bekannte Gesichter zu erkennen (z.B. "Master" oder "Jenny") und begrüßt diese.
- **Sehen**: Über Befehle wie "Was siehst du?" kann Haruko (falls konfiguriert) auf die Webcam oder den Bildschirminhalt zugreifen und diesen beschreiben.
- **Einrichtung**: Legen Sie Fotos von bekannten Personen in `backend/known_faces/` ab (z.B. `Jenny.jpg`).

## 8. Telegram Bot nutzen
Haruko ist auch unterwegs erreichbar:
- **Starten**: Suchen Sie Ihren Bot in Telegram und senden Sie `/start`.
- **Chat**: Schreiben Sie einfach wie mit einem Menschen.
- **Befehle**:
  - `/cam`: Haruko sendet ein aktuelles Foto (Webcam oder Screenshot) in den Chat. Ideal zur Überwachung.
  - `/help`: Zeigt Hilfe an.

## 9. PC-Steuerung & Apps
Sie können Ihren PC komplett per Sprache steuern:
- **Apps starten**: "Starte Spotify", "Starte Steam", "Starte Cyberpunk", "Öffne Yi IoT".
- **Navigation**: "Scrolle weiter", "Scrolle nach unten", "Seite zurück".
- **Lautstärke**: "Mach lauter", "Lautstärke auf 50%", "Ton aus".
- **Medien**: "Pause", "Weiter", "Stop" (steuert Spotify/YouTube im Hintergrund).
- **System**: "Fahr den PC herunter" (Vorsicht!), "Bildschirm sperren".

## 10. Mobile & Tablet Steuerung (Neu in v2.5)
Wenn Sie Haruko auf dem Handy/Tablet nutzen:
- **Interface**: Auf Tablets und Handys verschwindet die obere Leiste. Nutzen Sie den neuen **Apps-Button** (unten links im Chat), um auf Home, Kameras oder Einstellungen zuzugreifen.
- **Zurück-Button**: Ein neuer, schwebender Pfeil (unten links) in den Vollbild-Ansichten (Home/Kameras) bringt Sie sofort zum Chat zurück.
- **Scrollen**: "Scroll runter" -> Haruko scrollt die Chat-Seite.

## 11. Tablet Fernsteuerung (ADB)
Haruko kann Ihr Android-Tablet fernsteuern (z.B. für TikTok oder eBooks), wenn Sie gerade keine Hand frei haben:
1.  **Einrichtung**: Führen Sie `setup_adb.bat` am PC aus und koppeln Sie Ihr Tablet.
2.  **Nutzung**: Sagen Sie "Scrolle auf dem Tablet weiter" oder "Nächstes Video".
3.  **Technik**: Haruko simuliert Wisch-Gesten auf dem verbundenen Gerät.

## 12. Sekretär & Gedächtnis
Haruko hilft Ihnen im Alltag:
- **Timer**: "Stelle einen Timer auf 10 Minuten für Pizza."
- **Wecker**: "Weck mich morgen um 07:00 Uhr."
- **Notizen**: "Notiz: Milch und Eier kaufen."
- **Gedächtnis**: "Merk dir, dass mein Lieblingsessen Sushi ist." (Haruko speichert dies dauerhaft).
  - *Neu*: Haruko räumt ihr Gedächtnis nachts automatisch auf, fasst Fakten zusammen und löscht Veraltetes.
- **Wetter**: "Wie wird das Wetter morgen?"

## 13. Autonomes Lernen (Neu in v2.7)
Haruko kann sich nun selbst Wissen aneignen:
- **Lern-Befehl**: Sagen Sie z.B. "Lern mir etwas über Quantenphysik" oder "Recherchiere, wie man Sushi macht".
- **Ablauf**: Haruko startet eine Recherche, erstellt einen Guide und speichert diesen ab.
- **Abruf**: Später können Sie fragen "Wie macht man Sushi?" und Haruko nutzt das gespeicherte Wissen.

## 14. Netzwerk-Steuerung (WoL)
Haruko kann PCs im Netzwerk aufwecken:
- **Voraussetzung**: Der PC muss Wake-on-LAN (WoL) unterstützen und im BIOS aktiviert haben.
- **Befehl**: "Wecke den PC mit der MAC-Adresse AA:BB:CC:DD:EE:FF".
- **Scanner**: "Scanne das Netzwerk", um verfügbare Geräte zu finden.

## 15. Sprache ändern (Deutsch -> Englisch)
Standardmäßig spricht Haruko Deutsch. Um auf Englisch (oder andere Sprachen) zu wechseln, müssen 3 Dateien bearbeitet werden:

1.  **Persönlichkeit (Gehirn)**:
    - Datei: `backend/personality.py`.
    - Übersetzen Sie den `SYSTEM_PROMPT` ins Englische.
    - **Wichtig**: Entfernen Sie die Zeile `SPRACHE: Du antwortest AUSSCHLIESSLICH auf DEUTSCH.`

2.  **Stimme (TTS)**:
    - Datei: `backend/tts_cli.py`.
    - Ändern Sie `VOICE = "de-DE-AmalaNeural"` zu einer englischen Stimme wie `"en-US-AriaNeural"`.

3.  **Spracherkennung (Wakeword)**:
    - Datei: `frontend/src/App.tsx`.
    - Suchen Sie nach `recognition.lang = 'de-DE'` und ändern Sie es zu `'en-US'`.

## 16. Fehlerbehebung
- **Avatar bewegt sich nicht?** Prüfen Sie, ob das Backend läuft (`main.py`).
- **Kein Ton?** Prüfen Sie, ob `mpv` installiert ist und im Pfad liegt.
- **Tuya geht nicht?** Prüfen Sie die `devices.json` und Ihre IDs.
- **ADB Verbindung verloren?** Starten Sie `setup_adb.bat` erneut.

## 17. Danksagung & Credits

Dieses Projekt wurde entworfen, konzipiert und entwickelt von:

**Stephan Eck (Protheanreact)**
*Lead Developer & UI/UX Designer*

Vielen Dank für die Nutzung von Haruko AI!
