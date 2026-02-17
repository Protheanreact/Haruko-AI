# HARUKO SERVER INSTALLATION GUIDE (Fujitsu Mini-PC)

Hier ist die Schritt-für-Schritt Anleitung, um Haruko 1:1 auf deinen Fujitsu Server (Windows 11) zu übertragen.

## 1. VORBEREITUNG (Auf deinem jetzigen PC)
Stelle sicher, dass der Ordner `E:\moltbotback` sauber ist.
- Lösche ggf. temporäre Ordner wie `backend\__pycache__` (optional, spart Platz).
- Kopiere den **kompletten** Ordner `moltbotback` auf einen USB-Stick oder direkt über das Netzwerk auf den Server.

## 2. AUF DEM SERVER (Fujitsu)
Kopiere den Ordner an einen Ort deiner Wahl, z.B. `C:\moltbotback`.

### SCHRITT 1: Installation (Admin)
1. Gehe in den Ordner `C:\moltbotback`.
2. Rechtsklick auf **`setup_windows.bat`** -> **"Als Administrator ausführen"**.
3. **WICHTIG:** Das Skript macht alles automatisch:
   - Installiert Python 3.12 (falls fehlt).
   - Installiert Node.js (falls fehlt).
   - Installiert Ollama (falls fehlt).
   - Lädt die KI-Modelle (Llama 3 & Llava).
   - Installiert alle Python-Pakete (inkl. dem neuen `ddgs` für die Suche).
   - Legt optional den Ordner `C:\KI\haruko-whatsapp-bridge` an und erzeugt ein WhatsApp-Bridge-Template (nur auf deinem Server, ohne persönliche Daten).
   *Dauer: ca. 10-20 Minuten (je nach Internet).*

### SCHRITT 2: Autostart Einrichten (optional)
Damit Haruko immer läuft, auch nach einem Stromausfall/Neustart, kannst du einen Autostart über den Windows-Startup-Ordner einrichten:
1. Drücke `Win + R`, tippe `shell:startup` und bestätige.
2. Erstelle dort eine Verknüpfung zu `C:\moltbotback\start_haruko_windows.bat`.
3. Beim nächsten Login startet Haruko automatisch.

### SCHRITT 3: Erster Start & Test
1. Doppelklick auf **`start_haruko_windows.bat`**.
2. Es sollten sich **2 Fenster** öffnen:
   - Backend Server
   - Frontend Server
3. Öffne den Browser auf dem Server und gehe zu: `http://localhost:5173`.
   - Siehst du Haruko?
   - Bewegt sie sich?
   - Teste die Suche: "Was gibt es neues bei der Formel 1?"

## 3. ZUGRIFFS-DATEN
Du hast jetzt mehrere Wege, Haruko zu erreichen. Alle funktionieren gleichzeitig:

1. **Lokal am Server:** `http://localhost:5173`
2. **Im Heimnetzwerk (WLAN):** `http://[IP-DES-SERVERS]:5173`
   *(Finde die IP mit `ipconfig` heraus, z.B. 192.168.178.x)*
3. **Aus dem Internet (optional):**
   - Für externen Zugriff kannst du selbst einen Tunnel (z.B. Cloudflared) oder einen Reverse Proxy (z.B. nginx auf einem vServer) einrichten.
   - Standardmäßig richtet Haruko keinen automatischen Internet-Tunnel mehr ein.

## 4. PORTS & NETZWERK INFOS
Falls du im Router (FritzBox?) etwas freigeben willst (für LAN-Zugriff), hier sind die Ports:

- **Frontend (Webseite):** Port `5173`
- **Backend (API):** Port `8000`
- **Ollama (KI-Engine):** Port `11434`

**Zugriff im Heimnetzwerk (WLAN):**
Du brauchst keinen Tunnel. Rufe einfach die IP des Servers auf:
`http://[IP-DES-SERVERS]:5173`
(z.B. `http://192.168.178.50:5173`)

## 5. AUTOMATISCHE DIAGNOSE & REPARATUR (NEU!)
Wenn irgendetwas nicht funktioniert (z.B. fehlende Pakete, KI antwortet nicht), haben wir jetzt ein **"Selbstheilungs-Tool"**.

1. Öffne ein Terminal im Ordner `backend`.
2. Tippe: `python server_diagnose_fix.py`
3. Drücke Enter.

Das Tool prüft **alles** automatisch:
- Sind alle Python-Pakete da? (Installiert fehlende nach, z.B. `groq`)
- Läuft Ollama? (Startet es falls nicht)
- Fehlen KI-Modelle? (Lädt sie automatisch herunter)
- Stimmen die API-Keys? (Testet die Verbindung)

Wenn am Ende alles "Grün" (✅) ist, läuft der Server garantiert.

## CHECKLISTE BEI PROBLEMEN
- **Kamera geht nicht?** Prüfe, ob die IP der Kamera (`192.168.178.91`) vom Server aus erreichbar ist (`ping 192.168.178.91` in cmd).
- **Suche geht nicht?** Prüfe Internetverbindung am Server.
- **Haruko antwortet nicht?** Schau in das schwarze Backend-Fenster. Steht da ein Fehler?

Viel Erfolg!
