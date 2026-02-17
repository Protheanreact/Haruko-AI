<img width="425" height="634" alt="image" src="https://github.com/user-attachments/assets/5b99e79a-f57f-4ea4-bafe-e49eb7f5fc97" />

https://www.youtube.com/watch?v=-AfM5Uo-OS0

# 🌸 Haruko AI (v2.7.1)
### The "Phygital" Companion | Built for Efficiency

Haruko is an autonomous AI entity designed to bridge the gap between digital intelligence and physical presence. Optimized for **16GB CPU-only environments**, she proves that high-level agency doesn't require a GPU cluster.

---

## 🧠 Hybrid-Brain Architecture
Haruko orchestrates multiple "States of Mind":
* **Reasoning:** Google Gemini 2.0 Flash & NVIDIA NIM.
* **Memory:** Long-term SQLite FTS5 storage with autonomous nightly reflection.
* **Body:** 3D VRM integration with Real-time Lip-Sync.
* **Senses:** Local Vosk STT (switching to Piper/Whisper) & Computer Vision.

## 🛠 Project Structure
This repository contains the full "All-In-One" (AIO) setup:
* **Installation:** Use `setup_windows.bat` or `install_haruko_aio.ps1` for easy setup.
* **Guides:** See [SERVER_INSTALL_GUIDE.md](./SERVER_INSTALL_GUIDE.md) for headless deployment.
* **Roadmap:** Check [FUTURE_PLANS.md](./FUTURE_PLANS.md) for the path to v3.0.

## 📖 Documentation
- **[The Book of Haruko](./release/docs/THE_BOOK_OF_HARUKO.md):** The full technical evolution from scratch.
- **[Technical Fact Sheet](./release/docs/FACT_SHEET_HARUKO.md):** Deep dive into metrics and constraints.

## 📱 WhatsApp Integration (Local Bridge)

Haruko can be controlled via **WhatsApp Web** using a local bridge script.
There is no Meta Cloud API involved – everything runs on your own machine.

- A small Node.js script (`haruko-whatsapp.js`) uses:
  - `whatsapp-web.js`
  - `qrcode-terminal`
  - `axios`
- It logs into your WhatsApp account via QR code (*Linked Devices*).
- Incoming messages are forwarded to the FastAPI backend (`/whatsapp/incoming`).
- Haruko’s reply is sent back into the chat.

Security model:

- **Master number**: Full access without a prefix.
- **Foreign users**: Need a password prefix, e.g. `PASSWORD: turn on the lights`.
- **Loop protection**: The bridge ignores its own messages to avoid reply loops.

The Windows AIO installer (`install_haruko_aio.ps1`) can optionally:

- Create `C:\KI\haruko-whatsapp-bridge\`.
- Generate a template `haruko-whatsapp.js` with placeholder values for:
  - `MASTER_NUMBER = 'YOUR_MASTER_NUMBER_HERE'`
  - `FOREIGN_PASSWORD = 'CHANGE_ME_PASSWORD'`
- Install the required Node dependencies inside that folder.

After setup, you start Haruko as usual via `start_haruko_windows.bat` and scan the QR code
in the WhatsApp bridge window with your phone under **Linked Devices**.

---
**Built with [Trae AI](https://www.trae.ai/)** 🛠️  
*Pushing the limits of Indie-AI Development.*

⚠️ Note: This is a personal journey and a work in progress. I am sharing this for inspiration, not for benchmarking. Be kind! 🌸
