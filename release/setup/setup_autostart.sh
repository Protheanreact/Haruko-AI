#!/bin/bash

echo -e "\033[0;36mHaruko Autostart Setup\033[0m"
echo "----------------------"

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo ./setup_autostart.sh)"
  exit 1
fi

# Determine User and Path
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(getent passwd $REAL_USER | cut -d: -f6)
PROJECT_DIR="$USER_HOME/moltbotback"

echo "User: $REAL_USER"
echo "Project Dir: $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "\033[0;31mError: Project directory not found at $PROJECT_DIR\033[0m"
    echo "Please ensure you copied 'moltbotback' to your home folder."
    exit 1
fi

# Select Hardware Profile
echo -e "\nSelect your hardware profile:"
echo "1) High Power PC (NVIDIA GPU) -> Uses Llama 3 (8B)"
echo "2) Low Power / Orange Pi (NPU/CPU) -> Uses Llama 3.2 (3B)"
read -p "Enter choice [1 or 2]: " choice

MODEL="llama3"
if [ "$choice" = "2" ]; then
    MODEL="llama3.2"
    echo -e "\033[0;32mSelected: Low Power Profile (Llama 3.2)\033[0m"
else
    echo -e "\033[0;32mSelected: High Power Profile (Llama 3)\033[0m"
fi

# 1. Backend Service
echo -e "\nCreating Backend Service..."
cat > /etc/systemd/system/haruko-backend.service <<EOL
[Unit]
Description=Haruko AI Backend
After=network.target ollama.service

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR/backend
Environment="OLLAMA_MODEL=$MODEL"
ExecStart=$PROJECT_DIR/backend/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 2. Frontend Service
echo "Creating Frontend Service..."
cat > /etc/systemd/system/haruko-frontend.service <<EOL
[Unit]
Description=Haruko AI Frontend
After=network.target

[Service]
Type=simple
User=$REAL_USER
WorkingDirectory=$PROJECT_DIR/frontend
ExecStart=/usr/bin/npm run dev -- --host
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# 3. Reload and Enable
echo "Enabling Services..."
systemctl daemon-reload
systemctl enable haruko-backend haruko-frontend
systemctl restart haruko-backend haruko-frontend

echo -e "\n\033[0;32mSuccess! Haruko is now running and will start automatically on reboot.\033[0m"
echo "Backend Status: systemctl status haruko-backend"
echo "Frontend Status: systemctl status haruko-frontend"
