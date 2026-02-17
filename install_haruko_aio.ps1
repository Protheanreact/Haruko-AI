# Haruko AIO Installer
# Checks for Python, Node.js, Ollama and installs them if missing.
# Then installs project dependencies and pulls the AI model.

# 0. Admin Check
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Fordere Administrator-Rechte an..." -ForegroundColor Yellow
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot
if (!$scriptPath) { $scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition }

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "       HARUKO - ALL-IN-ONE INSTALLER" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Helper: Refresh Environment Variables without restart
function Refresh-Env {
    foreach($level in "Machine","User") {
        [Environment]::GetEnvironmentVariables($level).GetEnumerator() | ForEach-Object {
            if ($_.Name -ne "PSModulePath") {
                [Environment]::SetEnvironmentVariable($_.Name, $_.Value, "Process")
            }
        }
    }
    # Special handling for PATH to merge User and Machine paths
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machinePath;$userPath"
}

# 1. PYTHON CHECK & INSTALL
Write-Host "Prüfe Python..." -ForegroundColor White
try {
    $pyVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Python ist installiert: $pyVersion" -ForegroundColor Green
    } else { throw "Python not found" }
} catch {
    Write-Host "[INFO] Python fehlt. Lade herunter..." -ForegroundColor Yellow
    $pyUrl = "https://www.python.org/ftp/python/3.12.2/python-3.12.2-amd64.exe"
    $pyInstaller = "$env:TEMP\python_installer.exe"
    Invoke-WebRequest -Uri $pyUrl -OutFile $pyInstaller
    
    Write-Host "Installiere Python (Bitte warten)..." -ForegroundColor Yellow
    # /quiet = silent, InstallAllUsers=1 = System wide, PrependPath=1 = Add to PATH
    Start-Process -FilePath $pyInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0" -Wait
    
    Refresh-Env
    Write-Host "[OK] Python wurde installiert." -ForegroundColor Green
}

# 2. NODE.JS CHECK & INSTALL
Write-Host "Prüfe Node.js..." -ForegroundColor White
try {
    $nodeVersion = node --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Node.js ist installiert: $nodeVersion" -ForegroundColor Green
    } else { throw "Node not found" }
} catch {
    Write-Host "[INFO] Node.js fehlt. Lade herunter..." -ForegroundColor Yellow
    $nodeUrl = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    $nodeInstaller = "$env:TEMP\node_installer.msi"
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeInstaller
    
    Write-Host "Installiere Node.js (Bitte warten)..." -ForegroundColor Yellow
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$nodeInstaller`" /qn" -Wait
    
    Refresh-Env
    Write-Host "[OK] Node.js wurde installiert." -ForegroundColor Green
}

# 3. OLLAMA CHECK & INSTALL
Write-Host "Prüfe Ollama..." -ForegroundColor White
try {
    $ollamaVersion = ollama --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Ollama ist installiert: $ollamaVersion" -ForegroundColor Green
    } else { throw "Ollama not found" }
} catch {
    Write-Host "[INFO] Ollama fehlt. Lade herunter..." -ForegroundColor Yellow
    $ollamaUrl = "https://ollama.com/download/OllamaSetup.exe"
    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    Invoke-WebRequest -Uri $ollamaUrl -OutFile $ollamaInstaller
    
    Write-Host "Installiere Ollama (Bitte warten)..." -ForegroundColor Yellow
    Start-Process -FilePath $ollamaInstaller -ArgumentList "/silent" -Wait
    
    Refresh-Env
    Write-Host "[OK] Ollama wurde installiert." -ForegroundColor Green
}

# Ensure Ollama Service is running
Write-Host "Starte Ollama Service..." -ForegroundColor White
if (!(Get-Process "ollama app" -ErrorAction SilentlyContinue)) {
    # Try to start it in background
    Start-Process "ollama" "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

# 4. CONFIGURATION SETUP
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host "Konfiguriere Umgebung..." -ForegroundColor Cyan

# Backend .env
$envPath = "$scriptPath\backend\.env"
$envExample = "$scriptPath\backend\.env.example"
if (!(Test-Path $envPath)) {
    if (Test-Path $envExample) {
        Copy-Item $envExample $envPath
        Write-Host "[INFO] Erstelle .env aus .env.example" -ForegroundColor Yellow
        Write-Host "       WICHTIG: Bitte 'backend/.env' nach der Installation bearbeiten (API Keys)!" -ForegroundColor Yellow
    } else {
        Write-Host "[WARN] .env.example nicht gefunden!" -ForegroundColor Red
    }
} else {
    Write-Host "[OK] .env ist bereits vorhanden." -ForegroundColor Green
}

# 5. INSTALL DEPENDENCIES
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host "Installiere Projekt-Abhängigkeiten..." -ForegroundColor Cyan

# Backend
Write-Host "-> Backend (Python)..." -ForegroundColor White
Set-Location "$scriptPath\backend"
try {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "Pip install failed" }
    Write-Host "[OK] Backend fertig." -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Konnte Python Requirements nicht installieren." -ForegroundColor Red
    Write-Host "Fehler: $_" -ForegroundColor Red
    Read-Host "Drücke Enter..."
    exit
}

# Frontend
Write-Host "-> Frontend (Node.js)..." -ForegroundColor White
Set-Location "$scriptPath\frontend"
try {
    cmd /c "npm install"
    if ($LASTEXITCODE -ne 0) { throw "NPM install failed" }
    
    # Install localtunnel globally to avoid npx prompts
    Write-Host "-> Installiere Tunnel-Tool (localtunnel)..." -ForegroundColor White
    cmd /c "npm install -g localtunnel"
    
    Write-Host "[OK] Frontend fertig." -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Konnte NPM Pakete nicht installieren." -ForegroundColor Red
    Write-Host "Fehler: $_" -ForegroundColor Red
    Read-Host "Drücke Enter..."
    exit
}

# 5. PULL MODEL
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host "Lade KI-Modelle (Llama 3 & Llava)..." -ForegroundColor Cyan
Write-Host "Das kann einige Minuten dauern (je nach Internet)..." -ForegroundColor Gray

try {
    Write-Host "-> Pulling Llama 3..." -ForegroundColor White
    ollama pull llama3
    if ($LASTEXITCODE -ne 0) { throw "Ollama pull llama3 failed" }

    Write-Host "-> Pulling Llava (Vision)..." -ForegroundColor White
    ollama pull llava
    if ($LASTEXITCODE -ne 0) { throw "Ollama pull llava failed" }

    Write-Host "[OK] Modelle geladen." -ForegroundColor Green
} catch {
    Write-Host "[FEHLER] Konnte Modelle nicht laden. Ist Ollama gestartet?" -ForegroundColor Red
    Write-Host "Versuche manuell 'ollama pull llama3' und 'ollama pull llava' später." -ForegroundColor Yellow
}

# 6. WHATSAPP BRIDGE (OPTIONAL)
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host "WhatsApp Web Bridge (Optional)..." -ForegroundColor Cyan

$whatsappDir = "C:\KI\haruko-whatsapp-bridge"
if (Test-Path $whatsappDir) {
    Write-Host "[INFO] WhatsApp-Bridge-Ordner existiert bereits: $whatsappDir" -ForegroundColor Gray
} else {
    Write-Host "Erstelle WhatsApp-Bridge-Ordner unter $whatsappDir ..." -ForegroundColor White
    New-Item -ItemType Directory -Path $whatsappDir | Out-Null
}

$whatsappFile = Join-Path $whatsappDir "haruko-whatsapp.js"
if (!(Test-Path $whatsappFile)) {
    Write-Host "Erstelle Beispiel-Skript 'haruko-whatsapp.js' (bitte später anpassen)..." -ForegroundColor White
    $template = @'
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const MASTER_NUMBER = 'YOUR_MASTER_NUMBER_HERE';
const FOREIGN_PASSWORD = 'CHANGE_ME_PASSWORD';

const BACKEND_BASE = 'http://localhost:8000';

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

const botMessageIds = new Set();

client.on('qr', qr => {
    console.clear();
    console.log('WhatsApp QR-Code (scannen mit Handy, Verknüpfte Geräte):');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp-Bridge ist bereit.');
});

function extractForeignCommand(text) {
    if (!text) return null;
    const trimmed = text.trim();
    const lower = trimmed.toLowerCase();
    const pw = FOREIGN_PASSWORD.toLowerCase();
    if (lower.startsWith(pw)) {
        let rest = trimmed.slice(pw.length);
        if (rest.startsWith(':') || rest.startsWith('-') || rest.startsWith(' ')) {
            rest = rest.slice(1).trimStart();
        }
        rest = rest.trim();
        if (!rest) return null;
        return rest;
    }
    return null;
}

client.on('message_create', async msg => {
    if (msg.fromMe) {
        botMessageIds.add(msg.id._serialized);
    }
});

client.on('message', async msg => {
    try {
        if (botMessageIds.has(msg.id._serialized)) {
            return;
        }

        const chat = await msg.getChat();
        const contact = await msg.getContact();

        const isGroup = chat.isGroup;
        const isFromMaster = contact.id._serialized.includes(MASTER_NUMBER);

        let text = msg.body || '';
        let effectiveText = text;
        let isAuthorizedForeign = false;

        if (!isFromMaster) {
            const extracted = extractForeignCommand(text);
            if (!extracted) {
                return;
            }
            effectiveText = extracted;
            isAuthorizedForeign = true;
        }

        const effectiveIsMaster = isFromMaster || isAuthorizedForeign;
        if (!effectiveIsMaster) {
            return;
        }

        if (isGroup) {
            if (!effectiveIsMaster) {
                return;
            }
        }

        const payload = {
            sender: contact.pushname || contact.number || 'Unknown',
            chat_id: chat.id._serialized,
            message: effectiveText
        };

        const res = await axios.post(`${BACKEND_BASE}/whatsapp/incoming`, payload, { timeout: 60000 });
        const reply = res.data && res.data.reply ? res.data.reply : null;
        if (reply) {
            const sent = await msg.reply(reply);
            if (sent && sent.id && sent.id._serialized) {
                botMessageIds.add(sent.id._serialized);
            }
        }
    } catch (err) {
        console.error('Fehler in WhatsApp-Bridge:', err?.message || err);
    }
});

client.initialize();
'@
    Set-Content -Path $whatsappFile -Value $template -Encoding UTF8

    Write-Host "[HINWEIS] Bitte passe im WhatsApp-Skript MASTER_NUMBER und FOREIGN_PASSWORD an." -ForegroundColor Yellow
    Write-Host "         Datei: $whatsappFile" -ForegroundColor Yellow
} else {
    Write-Host "[INFO] WhatsApp-Skript existiert bereits, lasse es unverändert." -ForegroundColor Gray
}

Write-Host "Installiere WhatsApp-Bridge Node-Abhängigkeiten..." -ForegroundColor White
try {
    Push-Location $whatsappDir
    if (!(Test-Path "package.json")) {
        cmd /c "npm init -y"
    }
    cmd /c "npm install whatsapp-web.js qrcode-terminal axios"
    Write-Host "[OK] WhatsApp-Bridge-Abhängigkeiten installiert." -ForegroundColor Green
} catch {
    Write-Host "[WARN] Konnte WhatsApp-Bridge-Abhängigkeiten nicht vollständig installieren: $_" -ForegroundColor Yellow
    Write-Host "       Du kannst dies später manuell in $whatsappDir nachholen." -ForegroundColor Yellow
} finally {
    Pop-Location
}

# 7. YI IOT CAMERA SETUP
Write-Host "---------------------------------------------------" -ForegroundColor Gray
Write-Host "Kamera-Software (Yi IoT)..." -ForegroundColor Cyan

$yiSetup = "$scriptPath\YIIOTHomePCClientIntl_Setup.exe"
if (Test-Path $yiSetup) {
    Write-Host "Yi IoT Setup gefunden." -ForegroundColor White
    Write-Host "Dies wird benötigt, damit Haruko deine Kameras (Küche, etc.) sehen kann." -ForegroundColor Gray
    $response = Read-Host "Möchtest du die Kamera-App jetzt installieren? (j/n)"
    if ($response -match "j|y") {
        Write-Host "Starte Installer... Bitte folge den Anweisungen am Bildschirm." -ForegroundColor Yellow
        try {
            Start-Process -FilePath $yiSetup -Wait
            Write-Host "[OK] Installation abgeschlossen." -ForegroundColor Green
            Write-Host "---------------------------------------------------" -ForegroundColor Gray
            Write-Host "[WICHTIG] NACH DEM SETUP:" -ForegroundColor Magenta
            Write-Host "1. Starte die App 'Yi IoT' auf dem Server." -ForegroundColor Magenta
            Write-Host "2. Logge dich mit deinem Account ein." -ForegroundColor Magenta
            Write-Host "3. Lasse die App offen (nicht minimiert), damit Haruko den Screen sehen kann." -ForegroundColor Magenta
        } catch {
            Write-Host "[FEHLER] Konnte Installer nicht starten: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Überspringe Kamera-Installation." -ForegroundColor Gray
    }
} else {
    Write-Host "Kein Yi IoT Setup im Ordner gefunden (Optional)." -ForegroundColor Gray
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Green
Write-Host "   INSTALLATION ERFOLGREICH ABGESCHLOSSEN!" -ForegroundColor Green
Write-Host "===================================================" -ForegroundColor Green
Write-Host "Du kannst Haruko jetzt mit 'start_haruko_windows.bat' starten."
Write-Host ""
Read-Host "Drücke Enter zum Beenden..."
