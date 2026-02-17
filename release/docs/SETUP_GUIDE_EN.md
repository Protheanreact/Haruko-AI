# Installation Guide (Setup Guide)

## System Requirements
- **OS**: Windows 10/11 or Linux (Ubuntu 20.04+ recommended).
- **Hardware**: Minimum 8GB RAM (16GB recommended for local AI), CUDA-capable GPU recommended.
- **Software**:
  - Python 3.10 or newer.
  - Node.js (LTS Version).
  - Ollama (for AI).
  - FFmpeg (for audio processing, install via apt on Linux).

## Installation

### 1. Unpack Files
Extract the project archive to a desired location (e.g., `C:\Haruko` or `/opt/haruko`).

### 2. Install AI Models

#### Local AI (Ollama)
Download Ollama from [ollama.com](https://ollama.com) and install it.
Start Ollama and pull a model:
```bash
ollama pull llama3.1
```
*(Optional: `deepseek-r1:8b` for logic tasks)*

#### Cloud AI (Gemini - Recommended for Autonomy)
For best performance and features like **Memory Reflection (Maintenance)** and **Self-Learning**, Haruko uses Google Gemini.
- Get a free API Key from Google AI Studio.
- Add it to `backend/main.py` or as an environment variable.
- *Without this key, extended autonomy features will not work.*

### 3. Run Setup Script

The setup script is now fully automated and handles dependencies (like C++ Runtimes) and configuration.

#### Windows
1.  Navigate to the `release/setup` folder.
2.  Run:
    ```powershell
    .\setup_windows.ps1
    ```
    - **Language Selection**: The script will ask you to choose a language (DE or EN).
    - The script will automatically request Admin privileges to install system components.
    - It will ask for your API Keys (Gemini, Tuya, Telegram) and generate the configuration.
    *If scripts are disabled: run `Set-ExecutionPolicy RemoteSigned`.*

#### Linux / Ubuntu Server
1.  Navigate to the `release/setup` folder.
2.  Make the script executable:
    ```bash
    chmod +x setup_linux.sh
    ```
3.  Run it:
    ```bash
    ./setup_linux.sh
    ```
    - The script automatically installs necessary build tools (`cmake`, `build-essential`).

### 4. Configuration (Automated)
The setup script has already handled most settings.
- Check the generated `backend/.env` file if you need to make changes.
- **Frontend IP**:
  - Open `frontend/.env`.
  - Change `VITE_API_URL` to your server IP (e.g., `https://192.168.1.100:8000`).

## Starting
Start the Backend and Frontend (see How-To).

---
*Project Lead & Design: **Stephan Eck (Protheanreact)***
