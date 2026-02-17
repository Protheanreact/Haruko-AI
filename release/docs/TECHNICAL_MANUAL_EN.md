# Technical Manual - Haruko AI v2.8

## Overview
Haruko AI is a modular AI assistant featuring a 3D avatar, voice control, smart home integration (Tuya), and a modern web interface. The system consists of a Python backend (FastAPI) and a React frontend (Vite).
**Version 2.8 introduces full Multilanguage Support (German/English).**

## Architecture

### System Diagram (Haruko 2.7)

```mermaid
graph TD
    %% Styling
    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef backend fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef cloud fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef hardware fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef storage fill:#eceff1,stroke:#455a64,stroke-width:2px;

    %% User Layer
    User((User)) -->|Voice/Text| UI[Frontend UI\n(React/Vite)]
    User -->|Camera| VisionCam[MobileVision\n(WebRTC)]
    User -->|Telegram| TeleBot
    
    %% Frontend Layer
    subgraph Frontend [Frontend Layer (Browser / Tablet)]
        direction TB
        UI -->|Renders| Avatar[3D Avatar\n(VRM / Three.js)]
        UI -->|Sends Audio/Text| API_Client[Axios / Fetch]
        VisionCam -->|Posts Frames| API_Client
    end
    
    %% Backend Layer
    subgraph Backend [Backend Layer (Python / FastAPI)]
        direction TB
        API_Gateway[API Gateway\n(main.py)]
        
        %% Core Logic
        Brain[LLM Logic / Router]
        Personality[Personality Engine\n(System Prompts)]
        WakeWord[Wake Word Listener\n(Vosk Local)]
        
        %% Submodules
        VisionMod[Vision Module\n(FaceID / Analysis)]
        Secretary[Secretary Module\n(Timer/Notes/Weather)]
        PC_Control[PC Control\n(App Launcher / Audio)]
        TuyaMod[Tuya Smart Home\n(tinytuya)]
        AutoLoop[Autonomous Loop\n(Boredom/Phygital)]
        
        %% Connections
        API_Gateway --> Brain
        API_Gateway --> VisionMod
        API_Gateway --> Secretary
        API_Gateway --> PC_Control
        API_Gateway --> TuyaMod
        
        Brain --> Personality
        AutoLoop --> Brain
        WakeWord --> API_Gateway
        
        %% New Modules v2.7
        NetTools[Network Tools\n(Wake-on-LAN)]
        SelfLearn[Self-Learning\n(Gemini Generator)]
        
        API_Gateway --> NetTools
        API_Gateway --> SelfLearn
    end
    
    %% Cloud Services
    subgraph CloudServices [External / Cloud Services]
        GeminiFree[Gemini 2.0 Flash\n(Free Key - Primary)]
        Groq[Groq API\n(Llama 3 70B - Secondary)]
        OpenRouter[OpenRouter\n(Free Models - Tertiary)]
        GeminiPaid[Gemini 2.0 Flash\n(Paid Key - Backup)]
        Ollama[Ollama\n(Local Fallback)]
        TTS_Cloud[Edge-TTS\n(Neural Voices)]
        Search[DuckDuckGo\n(Pre-Search)]
        TeleBot[Telegram Bot\n(Remote Control)]
    end
    
    %% Storage Layer
    subgraph Storage [Data & Memory]
        MemDB[(Long-Term Memory\nJSON/SQLite)]
        RAG[(RAG Knowledge\nPDFs)]
        Faces[(Known Faces\nImages)]
    end

    %% Data Flow Interactions
    API_Client <-->|HTTP / WebSocket| API_Gateway
    TeleBot <-->|Thread| API_Gateway
    
    %% Backend to Cloud
    Brain -->|1. Request| GeminiFree
    Brain -->|2. Fallback| Groq
    Brain -->|3. Fallback| OpenRouter
    Brain -->|4. Backup| GeminiPaid
    Brain -->|5. Offline| Ollama
    Brain -->|Search Info| Search
    
    %% Backend to Storage
    Brain <--> MemDB
```
The backend runs via `main.py`, providing REST API endpoints and WebSocket streams.
- **Framework**: FastAPI (High Performance, Async).
- **AI Architecture (Hybrid v2.6)**: 
  - *Primary*: **Gemini Free** (Flash 2.0) - Priority for general queries (Key D).
  - *Secondary*: **Groq (Llama 3 70B)** - Extremely fast text generation.
  - *Tertiary*: **OpenRouter (Free Models)** - Fallback to various free models (DeepSeek, Qwen).
  - *Backup*: **Gemini Paid** (Flash 2.0) - Used only if free tiers fail.
  - *Offline Fallback*: **Ollama** (Local, e.g., Llama 3.1) in case of total network failure.
- **Speech-to-Text (STT)**:
  - *Local*: Vosk (Offline) as default.
- **Text-to-Speech (TTS)**: 
  - *Engine*: Edge-TTS (Online, High Quality Neural Voices).
  - *Tuning*: Special "Anime/Waifu" tuning (Pitch +25Hz, Rate +10%) for a lively voice.
- **Smart Home**: `tinytuya` for controlling Tuya devices via local network or cloud.
- **Tools & Agents**:
  - *Pre-Search*: Automatic web search (DuckDuckGo) for knowledge questions before LLM generation.
  - *Secretary*: Timer, Alarm, Notes, Weather (Open-Meteo).
  - *Vision*: Analysis of webcam images or screen sharing (via Gemini or local Llava).

### Vision & FaceID Subsystem
The system features advanced visual capabilities, implemented as a Hybrid Solution (Client-Push + Backend-Processing):
1.  **Client-Side Capture (`MobileVision.tsx`)**:
    - Uses HTML5 `getUserMedia` API to access the camera (smartphone/webcam).
    - Sends frames to `/api/vision/analyze` every 5 seconds (configurable).
2.  **Face Recognition (`vision.py`)**:
    - Uses `face_recognition` (dlib) to identify known persons.
    - Reference images are stored in `backend/known_faces/`.
3.  **Generative Vision**:
    - For commands like "What do you see?", the current frame is sent to the Multimodal Model (Gemini 2.0 Flash).

### Frontend (React/TypeScript)
The frontend is a Single Page Application (SPA) built with Vite.
- **Framework**: React 19.
- **Language**: TypeScript.
- **3D Avatar**: `@pixiv/three-vrm` and `@react-three/fiber` for rendering VRM models.
- **Communication**: Axios for API requests, Fetch API for streaming responses.
- **Design**: Custom CSS (Glassmorphism), Lucide icons.

## Core Components & Data Flow

1.  **Voice Input**:
    - *Frontend*: Microphone input is captured via MediaRecorder API. Audio blobs (WebM) are sent to `/process_audio`.
    - *Backend*: `ffmpeg` converts WebM to WAV. Vosk or Google Speech transcribes audio to text.

2.  **Processing (Brain)**:
    - **Pre-Search**: Checks if current info is needed (e.g., "Weather", "News"). If yes, performs a web search and injects results into context.
    - **Hybrid Generation**: Tries Gemini API first; falls back to local Ollama automatically on error.
    - A prompt template (in `personality.py`) defines the bot's character.

3.  **Response & Avatar**:
    - Text is sent to the frontend via Server-Sent Events or direct response.
    - The frontend triggers `/speak`. Backend generates audio with **Edge-TTS**.
    - The avatar (`VRMAvatar.tsx`) analyzes volume/vowels and animates the mouth (Lip-Sync).

4.  **Smart Home**:
    - Commands like "Turn on light" are detected via Regex in the backend.
    - `TuyaManager` (in `main.py`) sends commands to the Tuya Cloud or locally to the device IP.

## 7. Secretary & Memory (Memory 3.0)
The system features an advanced Long-Term Memory (LTM) based on **SQLite** (`memory.db`) to ensure data persistence and scalability.
- **Storage**: SQLite Database (`backend/memory.db`).
- **Reflexion (Memory Maintenance)**: 
  - An automated background process (`perform_memory_reflection` in `main.py`) checks the knowledge base every 24 hours.
  - All facts are sent to Gemini Pro to remove duplicates, merge similar facts, and delete outdated information.
  - This keeps the memory compact and relevant without manual intervention.
- **Migration**: An automated migration script (`memory_db.py`) converts old `secretary_data.json` files to the database structure upon startup.
- **Features**:
  - **Facts (LTM)**: `EXECUTE: memory --add "..."` saves user preferences permanently.
  - **Auto-Memory (New in v2.6)**: Haruko automatically analyzes conversations for important facts (e.g., "I like pizza") and saves them independently.
  - **RAG Search (New in v2.6)**: Haruko can actively search her memory (`search_memory`) to answer complex questions ("What do you know about my hobbies?").
  - **Notes**: Logbook for thoughts/tasks.
  - **Timers & Alarms**: Background loop in `main.py` checks for due timestamps every minute.

## 8. Autonomy & Network (New in v2.7)
- **Self-Learning (Auto-Knowledge)**:
  - If the bot detects a learning request (e.g., "Teach me quantum physics"), it starts a **Gemini research**.
  - **Process**: Research -> Generate Markdown Guide -> Save to `knowledge/` -> Auto-Indexing.
  - **Result**: The knowledge is immediately available for future RAG queries.
- **Network Control (Network Tools)**:
  - **Wake-on-LAN**: Haruko can wake up PCs in the local network (`EXECUTE: WAKE_PC [MAC]`).
  - **Scanner**: Can scan the network for active devices (ARP scan).
- **PDF Diagnostics**:
  - `debug_pdf.py`: A tool to analyze PDF files for text readability to ensure the RAG system works correctly.

## 10. Client Control & Tablet Bridge (ADB)
To allow Haruko to perform actions on the end device (Tablet/Phone), there are two methods:

### A. Frontend Bridge (Browser)
- **Concept**: The backend sends commands in the response text, which the frontend intercepts and executes locally.
- **Protocol**: `EXECUTE_CLIENT: [COMMAND]|[PARAMETER]`
- **Supported Commands**:
  - `open_url|URL`: Opens a new tab.
  - `scroll|down` / `scroll|up`: Scrolls the Haruko app itself.
  - `alert|Text`: System popup.

### B. ADB Bridge (Android Native Control)
For actions **outside** the browser (e.g., controlling TikTok app), Haruko uses the Android Debug Bridge (ADB).
- **Setup**: `setup_adb.bat` connects the Server (PC) to the Tablet via TCP/IP.
- **Mechanism**:
  - Haruko sends shell commands to the connected device.
  - Command: `adb shell input swipe 500 1500 500 500 300` (Simulates swipe up).
- **Benefit**: Allows control of ANY app, as long as the tablet is paired.

## 11. Credits

This project was designed, conceptualized, and developed by:

**Stephan Eck (Protheanreact)**
*Lead Developer & UI/UX Designer*

## 12. WhatsApp Web Bridge (Experimental, Local)

In addition to Telegram and the HTTP notification API, Haruko can be controlled
via a local **WhatsApp Web bridge**. This is an unofficial integration that
uses your existing WhatsApp account through the browser.

### Architecture

- **Bridge process (Node.js)**  
  - Recommended path: `C:\KI\haruko-whatsapp-bridge\haruko-whatsapp.js`  
  - Uses `whatsapp-web.js`, `qrcode-terminal` and `axios`.  
  - Logs in via QR code and keeps the session using `LocalAuth`.

- **Backend integration (FastAPI)**  
  - `GET /whatsapp/health` – simple health check for the bridge.  
  - `POST /whatsapp/incoming` – called by the bridge when a new message arrives.  
  - Internally calls `process_chat_generator` and returns:
    ```json
    { "reply": "<text to send back to WhatsApp>" }
    ```

### Security & Routing

- **Master number**  
  - Configured in the bridge script as `MASTER_NUMBER`.  
  - Messages from this number are treated as fully trusted commands.

- **Group chat**  
  - Typically a group called `Haruko`.  
  - Messages from the master are forwarded directly; other participants require a password.

- **Password for foreign users**  
  - Configured as `FOREIGN_PASSWORD` in the script.  
  - Syntax:
    - `PASSWORD: <command>`
    - `PASSWORD <command>`
  - The bridge strips the password and forwards only the command text to the backend.

- **Loop protection**  
  - The bridge stores IDs of all bot messages in a set.  
  - Incoming messages with these IDs are ignored to avoid infinite reply loops.

### Startup

On Windows, the bridge can be started together with backend and frontend
from the project root via scripts like `start_haruko_windows.bat`, or via a
separate Node.js process in `C:\KI\haruko-whatsapp-bridge\`.
