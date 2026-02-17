# Häufig gestellte Fragen (FAQ)

### 1. Warum bekomme ich eine Sicherheitswarnung im Browser?
Da das System ein selbst-erstelltes SSL-Zertifikat nutzt (um Mikrofon-Zugriff im Netzwerk zu erlauben), vertraut der Browser diesem nicht automatisch.
**Lösung**: Klicken Sie auf "Erweitert" und dann "Weiter zu ... (unsicher)". Das ist im privaten Heimnetzwerk sicher.

### 2. Mein Mikrofon funktioniert auf dem Handy nicht.
- Stellen Sie sicher, dass Sie `https://` nutzen (nicht `http://`). Browser blockieren Mikrofon-Zugriff auf unsicheren Seiten.
- Prüfen Sie, ob Sie dem Browser die Berechtigung erteilt haben.
- Wählen Sie im Dropdown-Menü das korrekte Mikrofon aus (manchmal ist "Standard" falsch zugewiesen).

### 3. Der Bot antwortet nicht.
- Läuft **Ollama**? Der Bot benötigt Ollama im Hintergrund.
- Läuft das **Backend**? Prüfen Sie das Terminal-Fenster auf Fehler.
- Ist die **IP-Adresse** korrekt? Prüfen Sie die `frontend/.env` Datei.

### 4. Smart Home Geräte reagieren nicht.
- Sind die `TUYA_ACCESS_ID` und das Secret in `main.py` korrekt?
- Sind die Geräte in der Tuya Cloud online?
- Starten Sie das Backend neu, um die Geräteliste zu aktualisieren.

### 5. Wie füge ich neue Avatare hinzu?
- Speichern Sie `.vrm` Dateien im Ordner `frontend/public/models/`.
- Passen Sie die Logik in `backend/main.py` (`/avatar-check`) an, um zu definieren, wann welcher Avatar geladen werden soll.

### 6. Was ist Auto-Memory?
Haruko hört im Gespräch zu und speichert wichtige Fakten (z.B. Ihren Namen, Hobbys) automatisch ab. Sie müssen nicht mehr explizit "Merk dir..." sagen. Das System entscheidet selbst, was relevant ist.

### 7. Wie funktioniert das Selbst-Lernen (Self-Learning)?
Wenn Sie Haruko bitten, ihr etwas beizubringen (z.B. "Lern mir..."), recherchiert sie das Thema via Gemini, erstellt einen internen Guide und speichert ihn in `knowledge/`. Ab dann kann sie Fragen dazu beantworten, ohne erneut zu suchen.

### 8. Wie nutze ich Haruko über WhatsApp?
Haruko kann über eine lokale WhatsApp-Web-Bridge mit Ihnen chatten:
- Stellen Sie sicher, dass der Server läuft und `start_haruko_windows.bat` gestartet wurde.
- Es öffnet sich ein Fenster "Haruko WhatsApp" mit einem QR-Code.
- Scannen Sie den QR-Code in WhatsApp unter **Verknüpfte Geräte**.
- Befehle:
  - Die Master-Nummer hat immer Vollzugriff.
  - Andere Personen können Befehle mit einem Passwort-Präfix schicken, z.B. `PASSWORT: Licht an`.

### 9. Wie kann ich die Sprache ändern?
Sie können die Sprache jederzeit ändern, indem Sie entweder:
- Das Setup-Skript (`setup_windows.ps1`) erneut ausführen und die Sprache wählen.
- Oder manuell die Datei `backend/.env` bearbeiten und die Zeile `LANGUAGE=EN` (für Englisch) oder `LANGUAGE=DE` (für Deutsch) anpassen. Starten Sie danach das Backend neu.
