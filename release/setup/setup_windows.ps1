# Haruko Setup Script for Windows

Write-Host "Haruko AI Setup - Windows" -ForegroundColor Cyan
Write-Host "--------------------------"

# 1. Check Prerequisites
$pythonVersion = python --version 2>$null
if (-not $?) {
    Write-Error "Python is not installed or not in PATH. Please install Python 3.10+."
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

$nodeVersion = node --version 2>$null
if (-not $?) {
    Write-Error "Node.js is not installed. Please install Node.js (LTS)."
    exit 1
}
Write-Host "Found Node: $nodeVersion" -ForegroundColor Green

# 1.1 Language Selection
$language = Read-Host "Choose Language / Sprache waehlen (DE/EN) [Default: DE]"
if ([string]::IsNullOrWhiteSpace($language)) { $language = "DE" }
$language = $language.ToUpper()
Write-Host "Selected Language: $language" -ForegroundColor Cyan

# 2. Setup Backend
Write-Host "`n[1/3] Setting up Backend..." -ForegroundColor Yellow
$backendPath = Join-Path (Get-Location) "..\..\backend"
if (-not (Test-Path $backendPath)) {
    Write-Error "Backend folder not found at $backendPath"
    exit 1
}

Push-Location $backendPath
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python Virtual Environment..."
    python -m venv venv
}

# Activate venv
.\venv\Scripts\Activate.ps1

Write-Host "Installing Python Dependencies..."
pip install -r ..\release\setup\backend_requirements.txt

# Set Language in .env
$envFile = ".env"
if (-not (Test-Path $envFile)) {
    New-Item -Path $envFile -ItemType File -Force
}
$envContent = Get-Content $envFile -Raw
if ($envContent -notmatch "LANGUAGE=") {
    Add-Content -Path $envFile -Value "`nLANGUAGE=$language"
} else {
    (Get-Content $envFile) -replace "LANGUAGE=.*", "LANGUAGE=$language" | Set-Content $envFile
}
Write-Host "Language set to $language in .env" -ForegroundColor Green

# 2.1 Check/Install Ollama Model
Write-Host "`n[2.1] Checking Ollama Model (llama3.1)..." -ForegroundColor Yellow
try {
    # Check if ollama is reachable and list models
    $ollamaList = ollama list
    if ($ollamaList -match "llama3.1") {
        Write-Host "Model 'llama3.1' found." -ForegroundColor Green
    } else {
        Write-Host "Model 'llama3.1' not found. Pulling now (this may take a while)..." -ForegroundColor Cyan
        ollama pull llama3.1
    }
} catch {
    Write-Warning "Could not connect to Ollama. Please ensure Ollama is running to download the model."
}

Pop-Location

# 3. Setup Frontend
Write-Host "`n[2/3] Setting up Frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path (Get-Location) "..\..\frontend"
if (-not (Test-Path $frontendPath)) {
    Write-Error "Frontend folder not found at $frontendPath"
    exit 1
}

Push-Location $frontendPath
Write-Host "Installing Node Modules..."
npm install
Pop-Location

# 4. Final Instructions
Write-Host "`n[3/3] Setup Complete!" -ForegroundColor Green
Write-Host "--------------------------"
Write-Host "To start the system:"
Write-Host "1. Ensure Ollama is running."
Write-Host "2. Run the 'start_all.bat' script (create it if missing)."
Write-Host "   - Backend: python main.py"
Write-Host "   - Frontend: npm run dev"
