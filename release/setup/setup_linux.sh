#!/bin/bash

echo -e "\033[0;36mHaruko AI Setup - Linux/Ubuntu\033[0m"
echo "-------------------------------"

# 1. Check Prerequisites
if ! command -v python3 &> /dev/null; then
    echo -e "\033[0;31mPython3 is not installed.\033[0m"
    exit 1
fi
echo -e "\033[0;32mFound Python: $(python3 --version)\033[0m"

if ! command -v node &> /dev/null; then
    echo -e "\033[0;31mNode.js is not installed.\033[0m"
    exit 1
fi
echo -e "\033[0;32mFound Node: $(node --version)\033[0m"

if ! command -v ffmpeg &> /dev/null; then
    echo -e "\033[0;33mFFmpeg not found. Attempting install...\033[0m"
    sudo apt-get update && sudo apt-get install -y ffmpeg portaudio19-dev python3-pyaudio
else
    echo -e "\033[0;32mFound FFmpeg\033[0m"
fi

# 2. Setup Backend
echo -e "\n\033[0;33m[1/3] Setting up Backend...\033[0m"
SCRIPT_DIR=$(dirname "$0")
ROOT_DIR="$SCRIPT_DIR/../.."
BACKEND_DIR="$ROOT_DIR/backend"

if [ ! -d "$BACKEND_DIR" ]; then
    echo "Backend directory not found!"
    exit 1
fi

cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    echo "Creating Python Virtual Environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "Installing Python Dependencies..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/backend_requirements.txt"

# 3. Setup Frontend
echo -e "\n\033[0;33m[2/3] Setting up Frontend...\033[0m"
FRONTEND_DIR="$ROOT_DIR/frontend"

if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Frontend directory not found!"
    exit 1
fi

cd "$FRONTEND_DIR"
echo "Installing Node Modules..."
npm install

# 4. Final Instructions
echo -e "\n\033[0;32m[3/3] Setup Complete!\033[0m"
echo "--------------------------"
echo "To start the system:"
echo "1. Ensure Ollama is running ('ollama serve')."
echo "2. Backend: cd backend && source venv/bin/activate && python3 main.py"
echo "3. Frontend: cd frontend && npm run dev -- --host"
