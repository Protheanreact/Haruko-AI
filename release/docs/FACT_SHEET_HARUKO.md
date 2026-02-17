# Haruko AI - Technical Fact Sheet
**Project:** Haruko AI (Project MoltBot)
**Developer:** Stephan Eck (Protheanreact)
**Version:** 2.10 (The Self-Awareness Update)
**Architecture:** Hybrid Cloud/Local (Edge-First)

---

## 🚀 Executive Summary
Haruko is a fully autonomous, **"Phygital" (Physical + Digital)** AI assistant designed to run on constrained hardware (16GB RAM, CPU-only). Unlike standard chatbots, Haruko possesses a **3D embodied presence**, **long-term memory**, and **direct control** over the host PC and IoT environment. 

The project demonstrates that high-level AI agency does not require H100 clusters—only smart orchestration of efficient local algorithms and strategic cloud API usage.

## 🛠️ Tech Stack & Architecture

### **Core Constraints**
*   **Hardware:** Fujitsu Mini-PC (Intel CPU, 16GB RAM, Integrated Graphics).
*   **Target:** Maximum autonomy with minimal resource footprint.

### **Backend (The Brain)**
*   **Language:** Python 3.12 (AsyncIO)
*   **Framework:** FastAPI (REST + WebSockets)
*   **Orchestration:** Multi-threaded Event Loop (Main Server + Background Services)
*   **LLM Strategy (Hybrid Hierarchical):**
    1.  **Primary:** Google Gemini 2.0 Flash (Low latency, High Context)
    2.  **Speed Fallback:** Llama 3 70B via Groq (Sub-second inference)
    3.  **Offline Fallback:** Ollama (Local Llama 3.1 8B, quantized)

### **Frontend (The Body)**
*   **Framework:** React 19 (Vite) + TypeScript
*   **3D Engine:** React Three Fiber (Three.js)
*   **Avatar Standard:** VRM 1.0 (VRMA Animations)
*   **Interface:** Glassmorphism UI, fully reactive to voice/mood.

## 🧩 Key Modules & Innovations

### **1. The Librarian (Self-Correction System)**
*   **Function:** Autonomous background thread that runs hourly.
*   **Capabilities:**
    *   Monitors system health (Disk, Network, API Latency).
    *   **Active Knowledge Maintenance:** Scans local RAG documents (Markdown) and uses LLMs to update/refine them based on new user interactions.
    *   Prevents "Memory Rot" by consolidating database entries.

### **2. Dynamic User Profiler (Empathy Engine)**
*   **Function:** Real-time psychological modeling of the user.
*   **Mechanism:** Analyzes conversation patterns to extract attributes (Mood, Style, Interests).
*   **Storage:** SQLite `user_profiles` table (JSON blobs).
*   **Application:** Dynamically injects personality cues into the System Prompt, allowing Haruko to adapt her tone (e.g., from Sarcastic to Supportive) instantly.

### **3. Vision & Senses**
*   **Eye:** Hybrid `face_recognition` (Local dlib) + Gemini Vision (Scene Understanding).
*   **Ear:** Vosk (Local Offline STT) for wake-word and command processing.
*   **Voice:** Edge-TTS (Neural) with regex-based emoji stripping for natural prosody.

### **4. Phygital Interaction**
*   **IoT:** Direct local control of Tuya devices via `tinytuya` (No cloud lag).
*   **PC Control:** Deep OS integration (App launching, Volume, Shutdown) via Python system calls.
*   **Network:** Wake-on-LAN capabilities to manage other devices in the local subnet.

## 📊 Performance Metrics (v2.10)
*   **Idle RAM Usage:** ~450MB (Backend) + ~300MB (Frontend)
*   **Voice-to-Voice Latency:** ~1.2s (avg)
*   **Cold Boot Time:** < 4.5s
*   **Operating Cost:** ~$0.00/month (Leveraging Free Tiers of Gemini/Groq + Local Compute)

## 🗺️ Roadmap to v3.0
The next phase focuses on **Local Sovereignty**:
1.  **Local Neural TTS:** Replacing Edge-TTS with **Piper/VITS** for offline, emotive synthesis.
2.  **Real-Time Vision:** Migrating from snapshot-based analysis to continuous stream processing (requires NPU/GPU acceleration).
3.  **Voice Cloning:** Few-shot finetuning for custom character voices.

---
*Generated for Developer Showcase / NVIDIA Inception Application*
