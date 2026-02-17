import os
import warnings
# Suppress annoying pkg_resources deprecation warning from pygame/others
warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")
import json
import re
import subprocess
import threading
import psutil
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import ollama
import google.generativeai as genai
import speech_recognition as sr
from personality import SYSTEM_PROMPT
import vosk
import sys
import queue
import pyaudio
import tinytuya
import edge_tts
import tempfile
import uuid
import numpy as np
import pickle
from cameras import camera_manager
# Feature Modules
try:
    from telegram_bot import HarukoTelegramBot
except ImportError:
    HarukoTelegramBot = None
import vision
import phygital
import secretary

import openai
# Global Phygital Manager
phygital_manager = None

# Global Vision Context (for LLM Awareness)
LATEST_VISION_CONTEXT = {"person": None, "timestamp": 0}

# Global Interaction Timestamp
last_interaction_time = time.time()
last_boredom_complaint = 0

def autonomous_loop():
    """Checks for boredom and triggers autonomous speech."""
    global last_interaction_time, last_boredom_complaint
    print("[AUTONOMOUS] Starting Boredom Monitor...")
    
    while True:
        time.sleep(60) # Check every minute
        
        try:
            now = time.time()
            hour = datetime.now().hour
            
            # Constraint: Only speak between 10:00 and 20:00 autonomously about boredom
            if 10 <= hour < 20:
                # Boredom Threshold: 3 Hours (10800s)
                if (now - last_interaction_time > 10800) and (now - last_boredom_complaint > 10800):
                    print("[AUTONOMOUS] Boredom detected!")
                    if phygital_manager:
                        phygital_manager.pending_reaction = "Master? Lebst du noch? Mir ist langweilig... [ACTION: SHOCK]"
                        last_boredom_complaint = now
        except Exception as e:
            print(f"[AUTONOMOUS ERROR] {e}")

# Tuya Config (Load from .env or fallback)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path) # Load environment variables from .env file explicitly

print(f"[SYSTEM] Loading .env from: {env_path}")
TUYA_ACCESS_ID = os.getenv("TUYA_ACCESS_ID", "")
TUYA_ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET", "")
TUYA_REGION = os.getenv("TUYA_REGION", "eu") # 'eu' for Europe

# GEMINI CONFIG
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"[GEMINI] Config Error: {e}")

# DEEPSEEK CONFIG
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
print(f"[DEEPSEEK] API Key Loaded: {'Yes' if DEEPSEEK_API_KEY else 'No'}")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
try:
    deepseek_client = openai.Client(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
except Exception as e:
    print(f"[DEEPSEEK] Config Error: {e}")

# GROQ CONFIG
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
try:
    groq_client = openai.Client(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
except Exception as e:
    print(f"[GROQ] Config Error: {e}")


class TuyaManager:
    def __init__(self):
        self.access_id = TUYA_ACCESS_ID
        self.access_secret = TUYA_ACCESS_SECRET
        self.region = TUYA_REGION
        self.devices_cache = {}
        
        # 1. Load from Config (Priority)
        self.load_from_config()
        
        # Initialisiere Cloud asynchron, um den Server-Start nicht zu blockieren
        if self.access_id != "DEINE_ACCESS_ID":
            print("[TUYA] Starte Geräte-Suche im Hintergrund...")
            threading.Thread(target=self.refresh_devices, daemon=True).start()
            
        # Start Autonomous Loop
        threading.Thread(target=autonomous_loop, daemon=True).start()

    def load_from_config(self):
        try:
             config_path = os.path.join(os.path.dirname(__file__), "devices_config.json")
             if os.path.exists(config_path):
                 with open(config_path, "r", encoding='utf-8') as f:
                     data = json.load(f)
                 
                 count = 0
                 for room in data.get("rooms", {}).values():
                     for dev in room.get("devices", []):
                         name = dev["name"].lower()
                         self.devices_cache[name] = {
                             "id": dev["id"],
                             "ip": dev.get("ip"),
                             "key": dev.get("key"),
                             "mapping": dev.get("dps_mapping", {}),
                             "version": "3.3"
                         }
                         count += 1
                 print(f"[TUYA] {count} Geräte aus Config geladen.")
        except Exception as e:
             print(f"[TUYA] Config Load Error: {e}")

    def refresh_devices(self):
        print("[TUYA] Aktualisiere Geräte-Liste von der Cloud...")
        regions_to_try = [self.region, 'we', 'us'] # Fallback regions: Central Europe, Western Europe, US
        
        for region in regions_to_try:
            try:
                print(f"[TUYA] Versuche Region: {region}...")
                c = tinytuya.Cloud(
                    apiRegion=region, 
                    apiKey=self.access_id, 
                    apiSecret=self.access_secret
                )
                devices = c.getdevices()
                
                if isinstance(devices, list) and len(devices) > 0:
                    self.region = region # Update correct region
                    print(f"[TUYA] Erfolg! Region ist '{region}'.")
                    
                    for dev in devices:
                        name = dev.get('name', 'Unbekannt').lower()
                        self.devices_cache[name] = {
                            "id": dev.get('id'),
                            "ip": dev.get('ip'),
                            "key": dev.get('key'),
                            "version": dev.get('version', '3.3')
                        }
                    print(f"[TUYA] {len(self.devices_cache)} Geräte erfolgreich geladen.")
                    return # Stop after success
                
            except Exception as e:
                print(f"[TUYA] Fehler in Region {region}: {e}")
        
        print("[TUYA] WARNUNG: Keine Geräte in allen geprüften Regionen (eu, we, us) gefunden.")


    def control(self, device_name, state="on"):
        name = device_name.lower()
        
        # Falls Cache leer, versuche zu laden
        if not self.devices_cache and self.access_id != "DEINE_ACCESS_ID":
            self.refresh_devices()
            
        if name not in self.devices_cache:
            # Suche nach Teilübereinstimmung (z.B. "Licht" in "Licht Wohnzimmer")
            found = False
            for cached_name in self.devices_cache:
                if name in cached_name:
                    name = cached_name
                    found = True
                    break
            if not found:
                return f"Fehler: Gerät '{device_name}' nicht im Tuya-Account gefunden."
        
        dev_info = self.devices_cache[name]
        dev_info = self.devices_cache[name]
        
        # STRATEGIE-WECHSEL: CLOUD FIRST (Zuverlässiger)
        try:
            print(f"[TUYA] Versuche Cloud-Steuerung für {name} ({dev_info['id']})...")
            c = tinytuya.Cloud(
                apiRegion=self.region, 
                apiKey=self.access_id, 
                apiSecret=self.access_secret
            )
            
            val = True if state == "on" else False
            
            # Wir probieren nacheinander die gängigsten Codes
            codes_to_try = []
            
            # Check for mapping from config
            mapping = dev_info.get("mapping", {})
            power_code = mapping.get("power")
            if power_code:
                codes_to_try.append(power_code)
                
            codes_to_try.extend(["switch_1", "switch_led", "led_switch", "on_off"])
            
            success = False
            last_res = {}
            
            for code in codes_to_try:
                cmd = {"commands": [{"code": code, "value": val}]}
                res = c.sendcommand(dev_info['id'], cmd)
                if res.get("success"):
                    success = True
                    break
                last_res = res
            
            if success:
                 return f"{name.capitalize()} wurde via CLOUD erfolgreich auf {state} geschaltet."
            
            # Wenn Cloud fehlschlägt, versuche Local als Fallback (nur wenn IP da ist)
            print(f"[TUYA] Cloud fehlgeschlagen ({last_res}). Versuche Local Fallback...")
            
            d = tinytuya.OutletDevice(dev_info['id'], dev_info['ip'], dev_info['key'])
            d.set_version(float(dev_info['version']))
            if state == "on":
                d.turn_on()
            else:
                d.turn_off()
            return f"{name.capitalize()} wurde via LOCAL Fallback auf {state} geschaltet."

        except Exception as e:
            return f"Fehler bei Tuya-Steuerung: {str(e)}"

tuya = TuyaManager()

# TELEGRAM CONFIG
# Erstelle einen Bot via @BotFather und trage den Token hier ein:
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "HIER_DEINEN_TELEGRAM_TOKEN_EINFUEGEN")

# Global objects
telegram_bot = None
phygital_manager = None

# Global queue for audio data
audio_queue = queue.Queue()

def audio_callback(in_data, frame_count, time_info, status):
    audio_queue.put(in_data)
    return (None, pyaudio.paContinue)

class WakeWordListener:
    def __init__(self, model_path, wake_words=["haruko", "hey haruko", "hallo haruko", "start", "harro", "hey harro", "harru", "hey harru"]):
        self.model = vosk.Model(model_path)
        self.wake_words = wake_words
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recognizer = None
        self.rate = 16000
        
        # Versuche ein funktionierendes Mikrofon zu finden
        self._find_working_device()

    def _find_working_device(self):
        print("\n[AUDIO] Suche nach funktionierendem Audio-Eingabegerät...")
        best_device_index = None
        
        # 1. Heuristic Search (Preferred Devices)
        print("[AUDIO] Scanne nach bevorzugten Geräten (Plantronics, USB, etc.)...")
        preferred_keywords = ['plantronics', 'usb', 'microphone', 'headset', 'mic']
        avoid_keywords = ['oculus', 'virtual', 'steam', 'nvidia', 'line', 'output', 'stereo mix']
        
        candidates = []
        for i in range(self.p.get_device_count()):
            try:
                info = self.p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    name = info['name'].lower()
                    print(f"  - Device {i}: {info['name']}")
                    
                    score = 0
                    for k in preferred_keywords:
                        if k in name: score += 10
                    for k in avoid_keywords:
                        if k in name: score -= 20
                    candidates.append((i, score, info['name']))
            except: pass
        
        # Sort by score desc
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        if candidates:
            best = candidates[0]
            if best[1] > 0: # Only pick if positive match
                best_device_index = best[0]
                print(f"[AUDIO] TREFFER: Bevorzuge Gerät {best_device_index} ('{best[2]}') mit Score {best[1]}.")
        
        # 2. Fallback: Windows Default (only if no good heuristic match)
        if best_device_index is None:
            try:
                 default_info = self.p.get_default_input_device_info()
                 print(f"[AUDIO] Kein Favorit gefunden. Nutze System-Standard: {default_info['name']} (Index {default_info['index']})")
                 best_device_index = default_info['index']
            except:
                 print("[AUDIO] Kein Standard-Gerät gefunden.")

        # 3. Last Resort: Any input device
        if best_device_index is None and candidates:
             best_device_index = candidates[0][0] # Take the one with highest score (even if negative/zero)
             print(f"[AUDIO] Notlösung: Nehme Index {best_device_index}")


        if best_device_index is not None:
             print(f"[AUDIO] Nutze Device-Index: {best_device_index}")
             
             # CRITICAL FIX: Initialize Recognizer
             self.recognizer = vosk.KaldiRecognizer(self.model, self.rate)
             self.device_index = best_device_index
             
             self.stream = self.p.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=self.rate,
                                      input=True,
                                      input_device_index=best_device_index,
                                      frames_per_buffer=8000,
                                      stream_callback=audio_callback)
        else:
            raise Exception("Kein funktionierendes Mikrofon am Server gefunden.")
    
    def pause(self):
        if self.stream and self.stream.is_active():
            print("[AUDIO] Pausiere Lauscher für Command-Aufnahme...")
            self.stream.stop_stream()
            # self.stream.close() # Keeping open might be unsafe if SR needs it closed

    def resume(self):
        if self.stream and not self.stream.is_active():
            print("[AUDIO] Setze Lauscher fort...")
            self.stream.start_stream()

    def listen(self, callback):
        if not self.stream:
            print("Kein Audio-Stream verfügbar.")
            return

        print(f"Lausche auf Triggerwörter: {self.wake_words} (Rate: {self.rate}Hz)...")
        self.stream.start_stream()
        try:
            while True:
                data = audio_queue.get()
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").lower()
                    if text:
                        print(f"[STT FINAL] '{text}'")
                    for word in self.wake_words:
                        if word in text:
                            print(f"Triggerwort '{word}' erkannt!")
                            # Pass self for control
                            callback(self)
                            self.recognizer.Reset()
                            break
                else:
                    # Debug: Show partial results to see if mic is working
                    partial = json.loads(self.recognizer.PartialResult())
                    p_text = partial.get("partial", "")
                    if p_text:
                         # Print overwrite to avoid spamming log too much
                         sys.stdout.write(f"\r[STT PARTIAL] {p_text}")
                         sys.stdout.flush()
                         
                         for word in self.wake_words:
                            if word in p_text:
                                print(f"\nTriggerwort '{word}' in Partial erkannt!")
                                callback(self)
                                self.recognizer.Reset()
                                break

        except KeyboardInterrupt:
            pass
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.p.terminate()

import winsound

def trigger_action(listener=None):
    print("\n[TRIGGER] Jarvis wurde gerufen!")
    # Feedback Beep (High-Low)
    winsound.Beep(1000, 200)
    winsound.Beep(1500, 200)
    
    speak("Ja, Sir?")
    
    # Pausiere Lauscher für exklusiven Zugriff
    if listener: listener.pause()

    # Kurz warten
    import time
    time.sleep(0.5)
    
    r = sr.Recognizer()
    mic_index = listener.device_index if listener else None
    
    # Nutze das GLEICHE Device wie der Listener
    try:
        with sr.Microphone(device_index=mic_index) as source:
            print(f"[TRIGGER] Höre zu auf Device {mic_index}...")
            r.adjust_for_ambient_noise(source, duration=0.5)
            try:
                # Lausche für max 5 Sekunden
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                print("[TRIGGER] Audio aufgenommen. Transkribiere...")
                text = r.recognize_google(audio, language="de-DE")
                print(f"[TRIGGER] Verstanden: '{text}'")
                
                # Da process_chat async ist, müssen wir es synchron ausführen
                import asyncio
                asyncio.run(process_chat(text, []))
                
            except sr.WaitTimeoutError:
                print("[TRIGGER] Timeout - nichts gehört.")
            except sr.UnknownValueError:
                print("[TRIGGER] Nichts verstanden.")
                speak("Ich habe Sie leider nicht verstanden, Sir.")
            except Exception as e:
                print(f"[TRIGGER] Fehler: {e}")
    finally:
        # Lauscher wieder fortsetzen
        if listener: listener.resume()



from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    global telegram_bot, phygital_manager
    print("[SYSTEM] Haruko Backend startet (Lifespan)...")

    # Init Phygital Manager
    try:
        phygital_manager = phygital.PhygitalManager()
        phygital_manager.start()
    except Exception as e:
        print(f"[PHYGITAL] Start fehlgeschlagen: {e}")

    # Init Telegram Bot
    if HarukoTelegramBot and TELEGRAM_TOKEN and "HIER_" not in TELEGRAM_TOKEN:
        print("[TELEGRAM] Konfiguriere Bot-Integration...")
        
        async def tele_llm(text, source="telegram"):
            full_res = ""
            # Wir nutzen einen leeren History-Kontext für Telegram
            async for chunk in process_chat_generator(text, []):
                full_res += chunk
            return full_res
            
        async def tele_vision(target):
            if "cam" in target.lower():
                return vision.capture_webcam() if hasattr(vision, 'capture_webcam') else None
            return vision.capture_screen()

        telegram_bot = HarukoTelegramBot(TELEGRAM_TOKEN, tele_llm, tele_vision)
        # Background Task für Polling starten
        asyncio.create_task(telegram_bot.start_polling())
    else:
        print("[TELEGRAM] Übersprungen (Kein Token konfiguriert oder Modul fehlt).")
    
    yield
    
    # --- SHUTDOWN LOGIC ---
    print("[SYSTEM] Haruko Backend fährt herunter...")
    if phygital_manager:
        phygital_manager.stop()
    if telegram_bot:
        await telegram_bot.stop()

app = FastAPI(title="Haruko Backend", lifespan=lifespan)

# --- KNOWLEDGE BASE (RAG) ---
class KnowledgeBase:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "kb")
        os.makedirs(self.base_dir, exist_ok=True)
        self.index_path = os.path.join(self.base_dir, "kb_index.pkl")
        self.docs = []
        self.embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self._load()
        # Auto-scan knowledge folder
        self.scan_directory()

    def scan_directory(self, directory="knowledge"):
        import os
        from pypdf import PdfReader
        
        if not os.path.exists(directory):
            try:
                os.makedirs(directory, exist_ok=True)
            except: pass
            return

        print(f"[KB] Scanne '{directory}' nach Dokumenten...")
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            doc_id = f"doc_{filename}"
            
            # Check if already indexed (by ID)
            if any(d.get('id') == doc_id for d in self.docs):
                continue 
            
            text = ""
            try:
                if filename.lower().endswith(".pdf"):
                    print(f"[KB] Lese PDF: {filename}...")
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        extract = page.extract_text()
                        if extract: text += extract + "\n"
                
                elif filename.lower().endswith(".txt"):
                    print(f"[KB] Lese TXT: {filename}...")
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                
                if text.strip():
                    print(f"[KB] Indiziere: {filename} ({len(text)} Zeichen)...")
                    self.upsert(text, doc_id=doc_id)
            except Exception as e:
                print(f"[KB] Fehler beim Lesen von {filename}: {e}")

    def _load(self):
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, "rb") as f:
                    self.docs = pickle.load(f)
        except Exception as e:
            print(f"[KB] Lade-Fehler: {e}")
            self.docs = []

    def _save(self):
        try:
            with open(self.index_path, "wb") as f:
                pickle.dump(self.docs, f)
        except Exception as e:
            print(f"[KB] Speicher-Fehler: {e}")

    def _embed(self, text: str):
        try:
            res = ollama.embeddings(model=self.embed_model, prompt=text)
            vec = np.array(res["embedding"], dtype=np.float32)
            norm = np.linalg.norm(vec) + 1e-10
            return vec / norm
        except Exception as e:
            print(f"[KB] Embedding-Fehler: {e}")
            return None

    def upsert(self, text: str, doc_id: Optional[str] = None):
        emb = self._embed(text)
        if emb is None:
            return {"status": "failed", "reason": "embedding_error"}
        if doc_id is None:
            doc_id = f"doc_{len(self.docs)+1}"
        replaced = False
        for i, d in enumerate(self.docs):
            if d["id"] == doc_id:
                self.docs[i] = {"id": doc_id, "text": text, "emb": emb}
                replaced = True
                break
        if not replaced:
            self.docs.append({"id": doc_id, "text": text, "emb": emb})
        self._save()
        return {"status": "ok", "id": doc_id, "replaced": replaced}

    def clear(self):
        self.docs = []
        self._save()
        return {"status": "ok"}

    def search(self, query: str, top_k: int = 3):
        if not self.docs:
            return []
        q = self._embed(query)
        if q is None:
            return []
        sims = []
        for d in self.docs:
            sims.append((d, float(np.dot(q, d["emb"]))))
        sims.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in sims[:top_k]]

kb = KnowledgeBase()

# --- KB ENDPOINTS ---
class KBUpsert(BaseModel):
    text: str
    id: Optional[str] = None

@app.post("/kb/upsert")
async def kb_upsert_endpoint(req: KBUpsert):
    res = kb.upsert(req.text, req.id)
    return res

@app.get("/kb/search")
async def kb_search_endpoint(query: str, k: int = 3):
    results = kb.search(query, top_k=k)
    return [{"id": d["id"], "text": d["text"]} for d in results]

@app.post("/kb/clear")
async def kb_clear_endpoint():
    return kb.clear()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: List[dict] = []

class SpeakRequest(BaseModel):
    text: str

class ToolCallRequest(BaseModel):
    command: str

class CameraConfigRequest(BaseModel):
    id: str
    name: str
    url: str

class NotificationRequest(BaseModel):
    app: str
    title: Optional[str] = None
    message: str
    priority: Optional[str] = "normal"

# TTS Queue
# TTS Worker removed - using direct subprocess for stability
import subprocess
import sys
import asyncio

# Global Control Variables
current_tts_process = None
stop_signal = False
last_interaction_time = 0.0 # Track last user interaction timestamp

def speak(text):
    # Use subprocess to isolate TTS from main thread/loop
    # preventing runAndWait hangs
    global current_tts_process
    
    # Stop existing process if running
    if current_tts_process and current_tts_process.poll() is None:
        try:
            current_tts_process.terminate()
            current_tts_process.wait(timeout=1)
        except:
            pass

    try:
        # Pass text via argument (careful with length) or stdin
        # Utilizing stdin for safety with long descriptions
        script_path = os.path.join(os.path.dirname(__file__), "tts_cli.py")
        
        # Start new process without blocking (no communicate)
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            text=True,
            encoding='utf-8' # Ensure utf-8
        )
        current_tts_process = process
        
        # Write to stdin and close to let it run
        if process.stdin:
            process.stdin.write(text)
            process.stdin.close()
            
    except Exception as e:
        print(f"[TTS ERROR] Subprocess failed: {e}")

async def process_chat_generator(message: str, history: List[dict]):
    global stop_signal, current_tts_process
    stop_signal = False # Reset stop signal
    
    # Check for Stop command immediately
    if message.strip().lower() in ["stop", "halt", "ruhe", "sei still", "schnauze", "aufhören", "stop!", "stopp"]:
        print("[BACKEND] Stop-Befehl per Sprache/Text erkannt.")
        if current_tts_process and current_tts_process.poll() is None:
            try:
                current_tts_process.terminate()
                print("[BACKEND] TTS Prozess beendet.")
            except: pass
        yield "Okay."
        return

    print(f"\n[BACKEND] Verarbeite Nachricht (Stream): '{message}'")
    global last_interaction_time
    import time
    last_interaction_time = time.time() # Update interaction timestamp
    try:
        # Get Phygital Status
        home_status = ""
        if phygital_manager:
            home_status = phygital_manager.get_home_status_summary()
        
        if not home_status:
            home_status = "Sensoren verbunden, warte auf erste Daten (ca. 60s)..."

        # Dynamically inject available devices into the prompt
        device_list = "Keine Geräte gefunden"
        if phygital_manager:
            device_list = phygital_manager.get_device_control_list()
        elif tuya and tuya.devices_cache:
            device_list = ", ".join(tuya.devices_cache.keys())
            
        tuya_instructions = f"""
\n# SMART HOME STATUS (ECHTZEIT):
{home_status}

# SMART HOME / TUYA INTELLIGENZ:
Du hast Zugriff auf folgende Geräte (Nach Raum): {device_list}.
REGELN:
1. Wenn der User sagt 'Schalte X an/aus' -> EXECUTE: tuya_control --device 'X' --state 'on'/'off'
2. Wenn der User sagt 'Sage Tuya [Kommand]', ist das IMMER ein Befehl -> EXECUTE...
3. Ignoriere Sarkasmus bei Smart Home Befehlen. Führe sie einfach aus.
Beispiel: 'Bett an' -> EXECUTE: tuya_control --device 'Bett' --state 'on'

# SEKRETÄR / TOOLS:
- Timer: 'Stelle Timer auf 10 Minuten' -> EXECUTE: timer --minutes 10
- Wecker: 'Weck mich um 8 Uhr' -> EXECUTE: alarm --time 08:00
- Notiz: 'Notiere: Milch kaufen' -> EXECUTE: note --add "Milch kaufen"
- Notizen lesen: 'Was habe ich notiert?' -> EXECUTE: note --read
- Wetter: 'Wie ist das Wetter?' oder 'Wie warm ist es?' -> EXECUTE: weather --city "Berlin" (oder die genannte Stadt)

WICHTIGE REGELN FÜR TOOLS:
1. Wenn du ein Tool nutzen musst (wie Wetter, Timer, Licht), nutze den Befehl 'EXECUTE: ...'.
2. Du darfst (und sollst!) dazu einen kurzen, passenden Kommentar (sarkastisch/witzig) schreiben.
3. Der Befehl kann am Anfang, Ende oder mitten im Text stehen.
4. Beispiel: "Na gut, wenn Sie zu faul sind, den Schalter zu drücken. EXECUTE: tuya_control --device 'Licht' --state 'on'"
"""

        auto_memory_instructions = """
\n# AUTO-MEMORY (Lernen):
Wenn der User eine wichtige persönliche Tatsache nennt, die du dir merken sollst, füge am Ende deiner Antwort einen Tag hinzu: [MEMORY: Der Fakt]
Beispiel: "Verstanden, ich merke mir das. [MEMORY: User mag Pizza]"
Der Tag wird dem User nicht angezeigt.
"""

        # --- VAULT INSTRUCTIONS INJECTION ---
        vault_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge", "Instructions_for_Vault.txt")
        vault_content = ""
        if os.path.exists(vault_file):
            try:
                with open(vault_file, "r", encoding="utf-8", errors="ignore") as f:
                    vault_content = f.read()
                print("[SYSTEM] Vault-Instruktionen geladen und injiziert.")
            except Exception as e:
                print(f"[SYSTEM] Fehler beim Laden der Vault-Instruktionen: {e}")

        # MEMORY INJECTION
        facts = secretary.secretary_service.get_facts()
        facts_text = ""
        if facts:
            facts_text = "\n\n### LANGZEITGEDÄCHTNIS (Fakten über den User):\n" + "\n".join([f"- {f}" for f in facts])
        
        # MORNING BRIEFING CHECK
        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")
        morning_instr = ""
        # Check if 05:00 - 11:00 and not briefed yet
        if 5 <= datetime.now().hour <= 11:
            if secretary.secretary_service.get_last_briefing_date() != today_str:
                morning_instr = "\n\n[MORNING PROTOCOL] Dies ist der erste Kontakt heute. Starte mit einem 'Guten Morgen', nenne Datum & Wetter (nutze EXECUTE: weather wenn nötig oder schätze) und gib eine motivierende Bemerkung."
                secretary.secretary_service.set_last_briefing_date(today_str)

        system_msg = {"role": "system", "content": SYSTEM_PROMPT + "\n\n### VAULT INSTRUCTIONS (PRIME DIRECTIVE):\n" + vault_content + "\n\n" + tuya_instructions + auto_memory_instructions + facts_text + morning_instr + "\n\n# WICHTIG: Wenn du ein Tool nutzen willst, füge 'EXECUTE: ...' einfach in deine Antwort ein. Du darfst Text davor/danach schreiben."}

        # RAG: Injektion von Wissensbasis-Dokumenten
        try:
            rag_results = kb.search(message, top_k=3)
            if rag_results:
                rag_text = "\n\n### WISSEN AUS DEM GEDÄCHTNIS (RAG):\n" + "\n".join([f"- {i+1}. {d['text'][:500]}" for i, d in enumerate(rag_results)]) + "\n### ENDE GEDÄCHTNIS\n"
                system_msg["content"] += rag_text
        except Exception as _e:
            print(f"[KB] RAG-Injektion Fehler: {_e}")
        
        formatted_history = []
        for h in history:
            role = "assistant" if h['role'] == "bot" else h['role']
            formatted_history.append({"role": role, "content": h['content']})
        
        # VISION LOGIC
        image_path = None
        # Default model (can be overridden by ENV)
        # Default model selection
        target_model = os.getenv("OLLAMA_MODEL", "llama3")
        
        msg_low = message.lower()
        print(f"[DEBUG] Prüfe Vision-Trigger für Nachricht: '{msg_low}'")
        
        # Expanded triggers for webcam
        vision_triggers = ["sieh mich an", "kamera", "webcam", "foto", "guck mal", "schau mich an", "was siehst du", "cam", "check mal", "prüfe", "ist"]
        screen_triggers = ["bildschirm", "screenshot", "screen", "desktop"]
        
        # Keywords that imply we should look at the screen (because the camera app is there)
        # Removed 'katzenklo' to prefer Phygital Sensor Data over Vision
        screen_monitoring_keywords = ["küche", "herd", "sauber", "wohnzimmer", "yi iot", "app", "fenster", "tür"]
        
        # SENSOR EXCLUSION: If user asks about temperature, ignore vision unless explicitly asked for camera
        sensor_keywords = ["warm", "kalt", "temperatur", "grad", "heizung", "luftfeuchtigkeit", "wetter"]
        is_sensor_query = any(k in msg_low for k in sensor_keywords)
        is_explicit_vision = any(k in msg_low for k in ["kamera", "foto", "bild", "screenshot", "cam", "webcam", "sieh", "schau", "guck"])

        # Check for specific camera request "Schau auf Kamera X"
        specific_cam_match = None
        if "kamera" in msg_low or "cam" in msg_low:
             # Match "Kamera Wohnzimmer" or "Cam Garten"
             for cam_id, cam_data in camera_manager.get_cameras().items():
                if cam_data['name'].lower() in msg_low:
                    specific_cam_match = cam_id
                    break

        if specific_cam_match:
            print(f"[DEBUG] Spezifische Kamera erkannt: {specific_cam_match}")
            image_path = camera_manager.get_snapshot(specific_cam_match)
            if not image_path:
                 print("[ERROR] Konnte Snapshot nicht erstellen.")
        
        # Logic update: If "Kitchen/Stove" etc. is mentioned with a vision word, use SCREEN capture (Mirroring)
        elif (any(t in msg_low for t in vision_triggers) and any(k in msg_low for k in screen_monitoring_keywords)) or any(t in msg_low for t in screen_triggers):
            # NEW: Check if this is actually a sensor query
            if is_sensor_query and not is_explicit_vision:
                 print(f"[DEBUG] Vision Trigger unterdrückt, da Sensor-Abfrage vermutet (Keywords: {sensor_keywords})")
            else:
                print(f"[DEBUG] Screen-Monitoring Trigger erkannt! (Keywords: {screen_monitoring_keywords})")
                try:
                    import vision
                    image_path = vision.capture_screen()
                except Exception as e:
                     print(f"[ERROR] Fehler beim Screenshot: {e}")

        elif any(t in msg_low for t in vision_triggers):
            # NEW: Check if this is actually a sensor query
            if is_sensor_query and not is_explicit_vision:
                 print(f"[DEBUG] Webcam Trigger unterdrückt, da Sensor-Abfrage vermutet.")
            else:
                print("[DEBUG] Webcam-Trigger erkannt!")
                try:
                    import vision
                    image_path = vision.capture_webcam()
                    if not image_path:
                        print("[ERROR] vision.capture_webcam() returned None")
                except Exception as e:
                    print(f"[ERROR] Fehler beim Import oder Aufruf von vision: {e}")
            
        if image_path:
            print(f"[BACKEND] Vision aktiviert (Model: llava). Bild: {image_path}")
            target_model = 'llava'
            # OVERRIDE System Prompt for Vision to avoid "I am text based" refusal
            system_msg = {"role": "system", "content": "Du bist ein KI-Assistent mit der Fähigkeit, Bilder zu sehen (Vision). Du siehst vermutlich einen Screenshot des Desktops, auf dem Kamera-Feeds (z.B. Küche, Wohnzimmer) zu sehen sind. Beschreibe das Bild präzise auf Deutsch und beantworte die Frage des Users anhand des Bildes."}
            # Add instruction for Vision
            message += " (ANALYSIERE DAS BILD: Was siehst du? Beantworte die Frage des Users basierend auf dem Bildinhalt.)"

        # --- PRE-SEARCH LOGIC (Auto-Search based on User Input) ---
        # Forces search if user asks for it, bypassing LLM decision
        search_triggers = ["suche", "google", "recherchiere", "infos zu", "was gibt es neues", "aktuell", "wetter"]
        # Don't search if it's a vision/camera request or simple greeting
        if any(t in msg_low for t in search_triggers) and not image_path and len(message) > 5:
            print(f"[BACKEND] Pre-Search Trigger erkannt für: '{message}'")
            try:
                # Try to import ddgs (handling rename)
                try:
                    from ddgs import DDGS
                except ImportError:
                    try:
                        from duckduckgo_search import DDGS
                    except ImportError:
                        DDGS = None
                
                if DDGS:
                    search_query = message # Use full message for context search
                    # Clean query slightly
                    for t in ["suche nach", "suche", "google", "bitte"]:
                        search_query = search_query.replace(t, "", 1)
                    
                    print(f"[BACKEND] Führe Web-Suche durch: {search_query.strip()}")
                    search_res = ""
                    with DDGS() as ddgs:
                        try:
                            # Retry loop
                            results = None
                            for attempt in range(2):
                                try:
                                    results = list(ddgs.text(search_query.strip(), max_results=3))
                                    break
                                except Exception:
                                    import time
                                    time.sleep(1)
                            
                            if results:
                                for i, r in enumerate(results):
                                    search_res += f"- {r['title']}: {r['body']} (URL: {r['href']})\n"
                            else:
                                search_res = "Keine Ergebnisse gefunden."
                        except Exception as ex:
                            search_res = f"Such-Fehler: {ex}"
                    
                    # Inject into System Prompt
                    if search_res:
                        print(f"[BACKEND] Suchergebnisse erhalten. Injiziere in Kontext.")
                        system_msg['content'] += f"\n\n### ECHTZEIT-INTERNET-WISSEN (Nutz dies für deine Antwort!):\n{search_res}\n### ENDE WISSEN\n"
            except Exception as e:
                print(f"[PRE-SEARCH ERROR] {e}")

        # --- PHYGITAL CONTEXT INJECTION (Fix for 'room' command) ---
        if phygital_manager:
            try:
                # Basic State
                p_state = phygital_manager.get_current_state()
                p_temp = getattr(phygital_manager, 'last_temp', 'N/A')
                
                # Format Device States
                dev_status = ""
                if hasattr(phygital_manager, 'device_states'):
                     for dev_id, dps in phygital_manager.device_states.items():
                         # Try to find name in config
                         name = dev_id
                         if hasattr(phygital_manager, 'config'):
                             for r_name, room in phygital_manager.config.get('rooms', {}).items():
                                 for d in room.get('devices', []):
                                     if d.get('id') == dev_id:
                                         name = f"{r_name} {d.get('name')}"
                         dev_status += f"- {name}: {dps}\n"
                
                phygital_context = f"\n\n### SMART HOME STATUS (AKTUELLE DATEN):\n"
                phygital_context += f"- Raum-Klima: {p_state} (Temp: {p_temp}°C)\n"
                if dev_status:
                    phygital_context += f"Geräte-Status:\n{dev_status}"
                phygital_context += "HINWEIS: Nutze diese Daten DIREKT. Führe KEINE 'room' oder 'status' Befehle aus, um sie zu prüfen. Du hast sie bereits hier.\n### ENDE STATUS\n"
                
                system_msg['content'] += phygital_context
                # print(f"[BACKEND] Phygital Context injiziert: Temp={p_temp}")
            except Exception as pe:
                print(f"[BACKEND] Fehler bei Phygital Context Injection: {pe}")
        
        # --- VISION CONTEXT INJECTION (FaceID) ---
        try:
            global LATEST_VISION_CONTEXT
            # Context valid for 2 minutes
            if LATEST_VISION_CONTEXT.get("person") and (time.time() - LATEST_VISION_CONTEXT.get("timestamp", 0) < 120):
                person_seen = LATEST_VISION_CONTEXT["person"]
                if person_seen == "Unknown":
                    vision_info = f"\n### VISION SENSOR (LIVE KAMERA DATEN) ###\nMein Mobile Vision Modul meldet aktuell: Eine Person ist sichtbar, aber nicht identifiziert (Unbekannt).\nWenn der User fragt 'Wer bin ich' oder 'Was siehst du', antworte basierend auf diesen Daten: 'Ich sehe dich über die Kamera, aber ich kenne dein Gesicht noch nicht. Bitte lade ein Foto in meinen 'known_faces' Ordner.'\nIgnoriere, dass du ein Text-Modell bist; diese Daten kommen von meinen Augen.\n"
                    # Weichere Formulierung für Unknown, damit sie nicht aggressiv wird ("Lügner, du bist nicht Master")
                    user_vision_hint = f" [SYSTEM-HINWEIS: Kamera erfasst ein Gesicht (Identität noch nicht verifiziert).]"
                else:
                    vision_info = f"\n### VISION SENSOR (LIVE KAMERA DATEN) ###\nMein Mobile Vision Modul hat erkannt: {person_seen}.\nWenn der User fragt 'Wer bin ich' oder 'Siehst du mich', antworte: 'Ja, ich sehe dich, {person_seen}!'.\nIgnoriere, dass du ein Text-Modell bist; diese Daten kommen von meinen Augen.\n"
                    user_vision_hint = f" [SYSTEM-HINWEIS: Die Kamera erkennt '{person_seen}' vor dem Gerät.]"
                
                system_msg['content'] += vision_info
                # Also append to message variable so it gets into user_msg
                message += user_vision_hint
                
                print(f"[BACKEND] Vision Context injiziert: {person_seen}")
        except Exception as ve:
            print(f"[BACKEND] Vision Context Error: {ve}")

        # -----------------------------------------------------------

        user_msg = {"role": "user", "content": f"{message} (ANTWORTE AUF DEUTSCH. BEI TOOLS: 'EXECUTE: ...')"}
        
        if image_path:
            user_msg['images'] = [image_path]

        messages = [system_msg] + formatted_history + [user_msg]
        
        # --- HYBRID LLM GENERATION (DeepSeek -> Groq -> Gemini -> Ollama) ---
        print(f"[BACKEND] Generiere Antwort (Ziel: {target_model})...")
        
        full_content_part1 = ""
        is_tool_call_detected = False
        buffer = ""
        BUFFER_SIZE = 250 
        buffer_flushed = False
        
        active_stream = None
        using_provider = "none"

        # Check for Image (Vision Requirement)
        has_image = False
        for m in messages:
            if 'images' in m and m['images']: has_image = True
        
        # ---------------------------------------------------------
        # PRIORITY 1: GEMINI FREE (Flash 2.0) - KEY D
        # ---------------------------------------------------------
        gemini_free_key = os.getenv("GEMINI_API_KEY_FREE")
        
        if active_stream is None and gemini_free_key:
            try:
                print(f"[BACKEND] Versuche Gemini FREE (Flash 2.0)...")
                genai.configure(api_key=gemini_free_key)
                
                gemini_history = []
                sys_instr = system_msg['content']
                
                for m in messages:
                    if m['role'] == 'system': continue
                    role = "model" if m['role'] in ["assistant", "bot"] else "user"
                    content_parts = [m['content']]
                    if 'images' in m and m['images']:
                        import PIL.Image
                        for img_path in m['images']:
                            try:
                                img = PIL.Image.open(img_path)
                                content_parts.append(img)
                            except: pass
                    gemini_history.append({"role": role, "parts": content_parts})
                
                g_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instr)
                g_response = g_model.generate_content(gemini_history, stream=True)
                
                def gemini_adapter(resp):
                    for chunk in resp:
                        if chunk.text: yield chunk.text
                        
                active_stream = gemini_adapter(g_response)
                using_provider = "gemini_free"
                print(f"[BACKEND] Gemini FREE antwortet.")
                
            except Exception as e:
                print(f"[BACKEND] Fehler bei Gemini FREE: {e}. Fallback...")

        # ---------------------------------------------------------
        # PRIORITY 2: GROQ (Text Only)
        # ---------------------------------------------------------
        if active_stream is None and not has_image and os.getenv("GROQ_API_KEY"):
            try:
                print(f"[BACKEND] Versuche Groq (Llama 3.3 70B)...")
                # Use global groq_client
                g_client = groq_client if 'groq_client' in globals() else openai.Client(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
                
                groq_msgs = []
                for m in messages:
                    role = m['role']
                    content = m['content']
                    groq_msgs.append({"role": role, "content": content})

                stream = g_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=groq_msgs,
                    stream=True
                )
                
                def groq_adapter(gen):
                    for chunk in gen:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content

                active_stream = groq_adapter(stream)
                using_provider = "groq"
                print(f"[BACKEND] Groq antwortet.")
                
            except Exception as e:
                print(f"[BACKEND] Fehler bei Groq: {e}. Fallback...")

        # ---------------------------------------------------------
        # PRIORITY 3: OPENROUTER (Free Models)
        # ---------------------------------------------------------
        if active_stream is None and not has_image and os.getenv("OPENROUTER_API_KEY"):
            try:
                print(f"[BACKEND] Versuche OpenRouter (Free Models)...")
                or_client = openai.Client(api_key=os.getenv("OPENROUTER_API_KEY"), base_url="https://openrouter.ai/api/v1")
                
                # List of free models to try in order
                free_models = [
                    "google/gemini-2.0-flash-exp:free",
                    "deepseek/deepseek-r1:free",
                    "meta-llama/llama-3.3-70b-instruct:free",
                    "qwen/qwen-2.5-coder-32b-instruct:free"
                ]
                
                or_msgs = []
                for m in messages:
                    or_msgs.append({"role": m['role'], "content": m['content']})

                for model_name in free_models:
                    try:
                        print(f"[BACKEND] OpenRouter Versuch: {model_name}...")
                        stream = or_client.chat.completions.create(
                            model=model_name,
                            messages=or_msgs,
                            stream=True,
                            extra_headers={
                                "HTTP-Referer": "https://moltbot.ai", 
                                "X-Title": "MoltBot"
                            }
                        )
                        
                        def openrouter_adapter(gen):
                            for chunk in gen:
                                if chunk.choices and chunk.choices[0].delta.content:
                                    yield chunk.choices[0].delta.content
                        
                        active_stream = openrouter_adapter(stream)
                        using_provider = f"openrouter/{model_name}"
                        print(f"[BACKEND] OpenRouter ({model_name}) antwortet.")
                        break # Success, stop trying models
                    except Exception as me:
                        print(f"[BACKEND] OpenRouter {model_name} fehlgeschlagen: {me}")
                        continue

            except Exception as e:
                print(f"[BACKEND] Fehler bei OpenRouter: {e}. Fallback...")

        # ---------------------------------------------------------
        # PRIORITY 4: GEMINI PAID (Key C) - Fallback
        # ---------------------------------------------------------
        gemini_paid_key = os.getenv("GEMINI_API_KEY_PAID")
        
        if active_stream is None and gemini_paid_key:
            try:
                print(f"[BACKEND] Versuche Gemini PAID (Flash 2.0)...")
                genai.configure(api_key=gemini_paid_key)
                
                # Re-build history only if not built (code dup but safe)
                gemini_history = []
                sys_instr = system_msg['content']
                
                for m in messages:
                    if m['role'] == 'system': continue
                    role = "model" if m['role'] in ["assistant", "bot"] else "user"
                    content_parts = [m['content']]
                    if 'images' in m and m['images']:
                        import PIL.Image
                        for img_path in m['images']:
                            try:
                                img = PIL.Image.open(img_path)
                                content_parts.append(img)
                            except: pass
                    gemini_history.append({"role": role, "parts": content_parts})
                
                g_model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instr)
                g_response = g_model.generate_content(gemini_history, stream=True)
                
                def gemini_adapter(resp):
                    for chunk in resp:
                        if chunk.text: yield chunk.text
                        
                active_stream = gemini_adapter(g_response)
                using_provider = "gemini_paid"
                print(f"[BACKEND] Gemini PAID antwortet.")
                
            except Exception as e:
                print(f"[BACKEND] Fehler bei Gemini PAID: {e}. Fallback...")

        # ---------------------------------------------------------
        # PRIORITY 4: OLLAMA (Local - Text & Vision)
        # ---------------------------------------------------------
        if active_stream is None:
            try:
                print(f"[BACKEND] Versuche lokales Modell (Ollama)...")
                target_model_final = "llava" if has_image else target_model
                
                active_stream_gen = ollama.chat(model=target_model_final, messages=messages, stream=True)
                def ollama_adapter(gen):
                    for chunk in gen:
                        yield chunk['message']['content']
                active_stream = ollama_adapter(active_stream_gen)
                using_provider = "ollama"
                print(f"[BACKEND] Ollama ({target_model_final}) antwortet.")
                
            except Exception as e:
                print(f"[BACKEND] Fehler bei Ollama: {e}.")

        if active_stream is None:
             print("[BACKEND] CRITICAL: Alle Provider fehlgeschlagen.")
             yield "Fehler: Ich konnte keine Verbindung zu meinen Gehirn-Modulen herstellen (DeepSeek, Groq, Gemini, Ollama alle tot)."
             return

        try:
            for part in active_stream:
                if stop_signal:
                    print("[BACKEND] Stop-Signal empfangen. Breche Generierung ab.")
                    yield "\n[ABGEBROCHEN]"
                    return

                # part is already the text string
                full_content_part1 += part
                
                # Check for Tool Call immediately (anywhere in stream)
                if "EXECUTE:" in full_content_part1:
                    is_tool_call_detected = True
                
                # FIX: Do not suppress output for tool calls. 
                # We want Haruko to speak while executing.
                # We just filter the command string out of the buffer below.
                
                # Buffering Logic to prevent "Preamble Leak" and hide Tags
                if not buffer_flushed:
                    buffer += part
                    # Clean buffer from tags dynamically (including MEMORY and EXECUTE commands)
                    buffer = re.sub(r'\[(wave|execute|love|angry|laugh|cry|blush|wink|MEMORY:[^\]]*)\]', '', buffer, flags=re.IGNORECASE)
                    # Also try to hide the raw EXECUTE line from the chat/speech if possible
                    buffer = re.sub(r'EXECUTE:\s*[^\n]+', '', buffer, flags=re.IGNORECASE)
                    
                    if len(buffer) >= BUFFER_SIZE:
                        # Buffer full -> Flush
                        yield buffer
                        buffer_flushed = True
                        buffer = "" # clear buffer
                else:
                    # Already flushed, just stream directly
                    # Also clean part here
                    part = re.sub(r'\[(wave|execute|love|angry|laugh|cry|blush|wink|MEMORY:[^\]]*)\]', '', part, flags=re.IGNORECASE)
                    part = re.sub(r'EXECUTE:\s*[^\n]+', '', part, flags=re.IGNORECASE)
                    yield part
                    
            # End of stream. If we have leftover buffer, yield it.
            if not buffer_flushed and buffer:
                buffer = re.sub(r'\[(wave|execute|love|angry|laugh|cry|blush|wink|MEMORY:[^\]]*)\]', '', buffer, flags=re.IGNORECASE)
                buffer = re.sub(r'EXECUTE:\s*[^\n]+', '', buffer, flags=re.IGNORECASE)
                yield buffer
                
        except Exception as e:
            # Check for Connection Reset / WinError 10054
            if "WinError 10054" in str(e) or "ConnectionResetError" in str(e):
                print(f"[STREAM ERROR] Client hat Verbindung getrennt (Stream 1): {e}")
                return # Stop generator gracefully

            # Check for Llava not found error
            is_llava_error = False
            # Check safely for ResponseError if available
            try:
                if isinstance(e, ollama.ResponseError) and "not found" in str(e) and "llava" in str(target_model):
                     is_llava_error = True
            except: pass
            
            if not is_llava_error and "not found" in str(e) and target_model == 'llava':
                 is_llava_error = True

            if is_llava_error:
                print(f"[BACKEND] Fehler: Llava Modell nicht gefunden. Fallback auf {os.getenv('OLLAMA_MODEL', 'llama3.2')}.")
                try:
                    # Fallback: Remove image and retry
                    if 'images' in user_msg: del user_msg['images']
                    target_model = os.getenv("OLLAMA_MODEL", "llama3.2")
                    full_content_part1 = ""
                    stream = ollama.chat(model=target_model, messages=messages, stream=True)
                    for chunk in stream:
                        part = chunk['message']['content']
                        full_content_part1 += part
                        yield part
                    yield "\n\n(Ich kann meine Augen (Llava) noch nicht finden. Ich lade sie wohl noch herunter. Aber ich höre dich.)"
                except Exception as ex:
                    print(f"[STREAM ERROR] Fehler im Fallback-Stream: {ex}")
                    return
            else:
                print(f"[STREAM ERROR] Unbekannter Fehler: {e}")
                return

        print(f"[BACKEND] Antwort 1 von {using_provider} erhalten.")
        print(f"[DEBUG] Content 1: {full_content_part1}")
        
        # Strict Command Parsing to avoid hallucinations
        # re module is already imported globally
        # Look for SEARCH: until end of line
        search_match = re.search(r'SEARCH:\s*([^\n\r]+)', full_content_part1)

        # Look for EXECUTE: until end of line
        cmd_match = re.search(r'EXECUTE:\s*([^\n\r]+)', full_content_part1)
        
        # Look for MEMORY tags
        memory_matches = re.findall(r'\[MEMORY:\s*([^\]]+)\]', full_content_part1, flags=re.IGNORECASE)
        for fact in memory_matches:
            try:
                print(f"[BACKEND] Auto-Memory: Speichere Fakt '{fact.strip()}'")
                secretary.secretary_service.add_fact(fact.strip())
            except Exception as me:
                print(f"[MEMORY ERROR] {me}")
        
        if search_match:
            query = search_match.group(1).strip().strip('`')
            print(f"[BACKEND] Starte Internet-Suche: {query}")
            
            try:
                # Try new package name first to avoid warnings
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS

                results_text = ""
                with DDGS() as ddgs:
                    # Retry logic for stability
                    try:
                        results = list(ddgs.text(query, max_results=3))
                    except Exception as e:
                        print(f"[SEARCH ERROR] Erster Versuch fehlgeschlagen: {e}. Warte kurz...")
                        import time
                        time.sleep(1)
                        results = list(ddgs.text(query, max_results=3))

                    if not results:
                        results_text = "Keine Ergebnisse gefunden."
                    else:
                        for i, r in enumerate(results):
                            results_text += f"{i+1}. {r['title']}: {r['body']} (URL: {r['href']})\n"
                
                tool_output = f"Suchergebnisse für '{query}':\n{results_text}"
            except Exception as e:
                tool_output = f"Fehler bei der Internet-Suche: {e}"

            print(f"DEBUG - Search Output: {tool_output[:200]}...")
            
            # Re-chat with output
            messages.append({"role": "assistant", "content": full_content_part1})
            messages.append({"role": "user", "content": f"SYSTEM: Hier sind die Suchergebnisse aus dem Internet: {tool_output}. Antworte dem User nun basierend auf diesen Informationen kurz auf DEUTSCH. Integriere die Fakten, aber bleib in deiner Rolle (Sarkastisch/Nett)."})
            
            full_content_part2 = ""
            try:
                # Reuse the provider logic? Or simple fallback.
                # For simplicity and stability, we try Gemini again if it was used, or fallback.
                # Since we don't have the reusable block as a function yet, let's copy the Gemini/Ollama logic briefly or just use Ollama for the follow-up (simpler).
                # Actually, better to use Gemini if available.
                
                stream2 = None
                if using_provider == "gemini":
                    try:
                        # Re-build Gemini history with new messages
                        # (Optimized: Just append to previous context if we had a session object, but we used generate_content)
                        # So we rebuild:
                        gem_hist_2 = []
                        sys_instr_2 = system_msg['content']
                        for m in messages:
                            if m['role'] == 'system': continue
                            r = "model" if m['role'] in ["assistant", "bot"] else "user"
                            gem_hist_2.append({"role": r, "parts": [m['content']]}) # No images in search follow-up usually
                        
                        g_model_2 = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instr_2)
                        resp2 = g_model_2.generate_content(gem_hist_2, stream=True)
                        def g_adapt_2(r):
                            for c in r: 
                                if c.text: yield c.text
                        stream2 = g_adapt_2(resp2)
                    except:
                        pass # Fallback to Ollama below
                
                if stream2 is None:
                    s2_gen = ollama.chat(model=target_model, messages=messages, stream=True)
                    def o_adapt_2(g):
                        for c in g: yield c['message']['content']
                    stream2 = o_adapt_2(s2_gen)

                for part in stream2:
                    full_content_part2 += part
                    yield part
            except Exception as e:
                print(f"[STREAM ERROR] Abbruch während Search Stream 2: {e}")

        elif cmd_match:
            raw_cmd = cmd_match.group(1).strip()
            # Clean command: Strip potential hallucinations starting with " - " or similar if they look like text
            # Heuristic: If " - " exists, and the part after is long (> 20 chars), it's likely a hallucination
            if " - " in raw_cmd:
                parts = raw_cmd.split(" - ", 1)
                if len(parts[1]) > 15: # Arbitrary threshold for "comment/text"
                    raw_cmd = parts[0]
            
            cmd = raw_cmd.strip().strip('"').strip("'")
            print(f"[BACKEND] Führe Shell-Befehl aus: {cmd}")
            
            tool_output = ""
            
            # Check for Tuya command (Case Insensitive & Permissive)
            if cmd.lower().startswith("tuya_control"):
                # re is globally imported
                # Try to find device between --device and --state (handling quotes or no quotes)
                # Matches: --device "Name" --state, --device 'Name' --state, --device Name --state
                dev_match = re.search(r'--device\s+["\']?([^"\']+?)["\']?\s+--state', cmd, re.IGNORECASE)
                
                # Fallback if --state is not present or at end
                if not dev_match:
                     dev_match = re.search(r'--device\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)

                state_match = re.search(r'--state\s+["\']?(\w+)["\']?', cmd, re.IGNORECASE)
                
                if dev_match and state_match:
                    device = dev_match.group(1).strip()
                    state = state_match.group(1).strip()
                    tool_output = tuya.control(device, state)
                else:
                    tool_output = f"Fehler: Ungültiges Tuya-Format (Cmd: {cmd})"
            
            # --- PC CONTROL (NEU) ---
            elif cmd.lower().startswith("volume"):
                import pc_control
                # volume --set 50
                set_match = re.search(r'--set\s+(\d+)', cmd, re.IGNORECASE)
                # volume --change +10 / -10
                change_match = re.search(r'--change\s+([+-]?\d+)', cmd, re.IGNORECASE)
                
                if set_match:
                    tool_output = pc_control.set_volume(int(set_match.group(1)))
                elif change_match:
                    tool_output = pc_control.change_volume(int(change_match.group(1)))
                else:
                    tool_output = "Fehler: Ungültiger Volume-Befehl (nutze --set oder --change)."

            elif cmd.lower().startswith("media"):
                import pc_control
                # media --action play
                action_match = re.search(r'--action\s+["\']?(\w+)["\']?', cmd, re.IGNORECASE)
                if action_match:
                    tool_output = pc_control.media_action(action_match.group(1))
                else:
                    tool_output = "Fehler: Media-Action fehlt."

            elif cmd.lower().startswith("launch"):
                import pc_control
                # launch --app spotify
                app_match = re.search(r'--app\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)
                if app_match:
                    tool_output = pc_control.launch_app(app_match.group(1))
                else:
                    tool_output = "Fehler: App-Name fehlt."

            elif cmd.lower().startswith("scroll"):
                import pc_control
                # scroll --direction down
                dir_match = re.search(r'--direction\s+["\']?(\w+)["\']?', cmd, re.IGNORECASE)
                direction = dir_match.group(1) if dir_match else "down"
                tool_output = pc_control.scroll(direction)

            elif cmd.lower().startswith("scroll"):
                import pc_control
                # scroll --direction down
                dir_match = re.search(r'--direction\s+["\']?(\w+)["\']?', cmd, re.IGNORECASE)
                direction = dir_match.group(1) if dir_match else "down"
                tool_output = pc_control.scroll(direction)

            elif cmd.lower().startswith("adb_scroll"):
                import pc_control
                # adb_scroll --direction down
                dir_match = re.search(r'--direction\s+["\']?(\w+)["\']?', cmd, re.IGNORECASE)
                direction = dir_match.group(1) if dir_match else "down"
                tool_output = pc_control.adb_scroll(direction)

            elif cmd.lower().startswith("stats"):
                try:
                    import pc_control
                    tool_output = pc_control.get_system_stats_text()
                except ImportError:
                    tool_output = "Fehler: Modul 'pc_control' oder 'GPUtil' fehlt. Bitte 'pip install GPUtil' ausführen."
                except Exception as e:
                    tool_output = f"Fehler beim Abrufen der System-Stats: {e}"

            # --- SECRETARY TOOLS ---
            elif cmd.lower().startswith("timer"):
                match = re.search(r'--minutes\s+(\d+)', cmd, re.IGNORECASE)
                if match:
                    tool_output = secretary.secretary_service.set_timer(int(match.group(1)))
                else:
                    tool_output = "Fehler: Minuten fehlen."

            elif cmd.lower().startswith("alarm"):
                match = re.search(r'--time\s+(\d{1,2}:\d{2})', cmd, re.IGNORECASE)
                if match:
                    tool_output = secretary.secretary_service.set_alarm(match.group(1))
                else:
                    tool_output = "Fehler: Zeitformat HH:MM fehlt."

            elif cmd.lower().startswith("memory"):
                # memory --add "User mag keine Pilze"
                if "--add" in cmd:
                    text_match = re.search(r'--add\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)
                    if text_match:
                        tool_output = secretary.secretary_service.add_fact(text_match.group(1))
                    else:
                        tool_output = "Fehler: Kein Text für --add."
                elif "--delete" in cmd:
                    text_match = re.search(r'--delete\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)
                    if text_match:
                         tool_output = secretary.secretary_service.delete_fact(text_match.group(1))
                    else:
                        tool_output = "Fehler: Kein Text für --delete."
                elif "--read" in cmd:
                     facts = secretary.secretary_service.get_facts()
                     tool_output = "Gespeicherte Fakten:\n" + "\n".join(facts)
                else:
                    tool_output = "Fehler: Nutze --add, --delete oder --read."

            elif cmd.lower().startswith("note"):
                if "--add" in cmd:
                    text_match = re.search(r'--add\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)
                    if text_match:
                        tool_output = secretary.secretary_service.add_note(text_match.group(1))
                    else:
                         tool_output = "Fehler: Leere Notiz."
                elif "--read" in cmd:
                    tool_output = secretary.secretary_service.get_notes()

            elif cmd.lower().startswith("wake"):
                # EXECUTE: wake --mac AA:BB:CC...
                mac_match = re.search(r'--mac\s+["\']?([0-9a-fA-F:.-]+)["\']?', cmd)
                if mac_match:
                    tool_output = phygital.send_magic_packet(mac_match.group(1))
                else:
                    tool_output = "Fehler: MAC-Adresse fehlt. Nutze --mac XX:XX:XX..."

            elif cmd.lower().startswith("weather"):
                match = re.search(r'--city\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)
                city = match.group(1) if match else "Berlin"
                tool_output = secretary.secretary_service.get_weather(city)

            elif cmd.lower().startswith("camera"):
                # camera --view "Wohnzimmer"
                match = re.search(r'--view\s+["\']?([^"\']+)["\']?', cmd, re.IGNORECASE)
                target = match.group(1) if match else None
                
                # Finde Kamera ID basierend auf Name oder ID
                cam_id = None
                cams = camera_manager.get_cameras()
                
                if target:
                    # Direkter ID Match?
                    if target in cams:
                        cam_id = target
                    else:
                        # Suche nach Name
                        for cid, cdata in cams.items():
                            if target.lower() in cdata['name'].lower():
                                cam_id = cid
                                break
                else:
                    # Keine Angabe? Nimm die erste
                    if cams:
                        cam_id = list(cams.keys())[0]

                if cam_id:
                    snap_path = camera_manager.get_snapshot(cam_id)
                    if snap_path:
                        # ANALYSIERE MIT LLAVA
                        try:
                            print(f"[VISION] Sende Bild an Llava: {snap_path}")
                            res = ollama.chat(
                                model='llava',
                                messages=[{
                                    'role': 'user',
                                    'content': 'Beschreibe detailliert was du auf diesem Bild siehst.',
                                    'images': [snap_path]
                                }]
                            )
                            desc = res['message']['content']
                            tool_output = f"BILD-ANALYSE ({cams[cam_id]['name']}): {desc}"
                        except Exception as e:
                            tool_output = f"Fehler bei der Bildanalyse (Llava): {e}"
                    else:
                        tool_output = "Fehler: Konnte kein Bild von der Kamera abrufen."
                else:
                    tool_output = "Fehler: Kamera nicht gefunden oder keine Kameras konfiguriert."

            elif cmd.lower().startswith("wake"):
                # EXECUTE: wake --mac AA:BB:CC...
                mac_match = re.search(r'--mac\s+["\']?([0-9a-fA-F:.-]+)["\']?', cmd)
                if mac_match:
                    tool_output = network_tools.send_magic_packet(mac_match.group(1))
                else:
                    tool_output = "Fehler: MAC-Adresse fehlt. Nutze --mac XX:XX:XX..."

            else:
                # Normal shell command
                try:
                    # Fix common quote errors in commands (e.g. wiki --search "NSFW)
                    if cmd.count('"') % 2 != 0:
                        cmd += '"'
                    if cmd.count("'") % 2 != 0:
                        cmd += "'"
                    
                    # errors='ignore' prevents decoding crashes on special chars
                    result = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=15, encoding='cp850', errors='ignore')
                    tool_output = result.stdout.strip() or result.stderr.strip()
                except subprocess.TimeoutExpired:
                    yield "\n\n(Der Befehl hat zu lange gedauert, Master.)"
                except Exception as e:
                    print(f"Fehler bei Tool-Ausführung: {e}")
                    tool_output = f"Fehler: {e}"

            if not tool_output:
                tool_output = "[KEINE AUSGABE / ERFOLGREICH]"
            
            print(f"DEBUG - Tool Output: {tool_output[:100]}...")
            
            # Re-chat with output
            messages.append({"role": "assistant", "content": full_content_part1})
            messages.append({"role": "user", "content": f"Resultat der Ausführung: {tool_output}. Antworte nun kurz auf DEUTSCH. WICHTIG: Integriere die Fakten/Daten aus dem Resultat in deine Antwort, aber verpacke sie in deine aktuelle Stimmung (sarkastisch, lieb oder genervt, wie es passt). Der User will die Information UND deine Meinung."})
            
            full_content_part2 = ""
            try:
                stream2 = None
                
                # 1. Try Groq for follow-up (if used previously or available)
                if using_provider == "groq":
                    try:
                        from groq import Groq
                        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                        # Re-build Groq messages
                        groq_msgs_2 = []
                        for m in messages:
                             if m['role'] == 'system':
                                 groq_msgs_2.append({"role": "system", "content": m['content']})
                             elif m['role'] in ["user", "assistant"]:
                                 groq_msgs_2.append({"role": m['role'], "content": m['content']})
                        
                        stream = client.chat.completions.create(
                            messages=groq_msgs_2,
                            model="llama-3.3-70b-versatile",
                            stream=True,
                        )
                        def groq_adapter_2(gen):
                            for chunk in gen:
                                if chunk.choices[0].delta.content:
                                    yield chunk.choices[0].delta.content
                        stream2 = groq_adapter_2(stream)
                    except Exception as ge:
                         print(f"[BACKEND] Groq Folgeantwort fehlgeschlagen: {ge}. Fallback auf Ollama.")

                # 2. Try Gemini for follow-up
                if stream2 is None and using_provider == "gemini":
                    try:
                        # Re-build Gemini history for follow-up with tool output
                        gem_hist_2 = []
                        sys_instr_2 = system_msg['content']
                        for m in messages:
                            if m['role'] == 'system':
                                continue
                            r = "model" if m['role'] in ["assistant", "bot"] else "user"
                            gem_hist_2.append({"role": r, "parts": [m['content']]})
                        g_model_2 = genai.GenerativeModel('gemini-2.0-flash', system_instruction=sys_instr_2)
                        resp2 = g_model_2.generate_content(gem_hist_2, stream=True)
                        def g_adapt_2(r):
                            for c in r:
                                if c.text:
                                    yield c.text
                        stream2 = g_adapt_2(resp2)
                    except Exception as _ge:
                        print(f"[BACKEND] Gemini Folgeantwort fehlgeschlagen: {_ge}. Fallback auf Ollama.")
                if stream2 is None:
                    s2_gen = ollama.chat(model=target_model, messages=messages, stream=True)
                    def o_adapt_2(g):
                        for c in g:
                            yield c['message']['content']
                    stream2 = o_adapt_2(s2_gen)
                for part in stream2:
                    full_content_part2 += part
                    yield part
            except Exception as e:
                print(f"[STREAM ERROR] Abbruch während Stream 2: {e}")
            
            # REMOVED: speak(full_content_part2) - Client triggers TTS now

    except Exception as e:
        print(f"Fehler in process_chat_generator: {e}")
        yield f"Entschuldigung, Master, mein Gehirn hat gerade einen Schluckauf: {e}"

async def process_chat(message: str, history: List[dict]):
    full_text = ""
    async for chunk in process_chat_generator(message, history):
        full_text += chunk
    return full_text

@app.post("/chat_stream")
async def chat_stream_endpoint(request: ChatRequest):
    return StreamingResponse(process_chat_generator(request.message, request.history), media_type="text/plain")

@app.post("/chat")
async def chat(request: ChatRequest):
    content = await process_chat(request.message, request.history)
    return {"response": content}

async def generate_tts_file(text: str):
    # Optimierte "Waifu"-Settings für Edge-TTS (ohne RVC)
    # de-DE-AmalaNeural ist bereits sehr gut, aber wir machen sie etwas jünger/schneller
    VOICE = "de-DE-AmalaNeural"
    RATE = "+20%"  # Schneller = Energetischer
    PITCH = "+35Hz" # Höher = Jünger/Weiblicher
    
    # 1. Strip EXECUTE commands
    clean_text = text.split("EXECUTE:")[0]
    
    # 2. Strip Action Tags [ACTION: ...] and Mood Tags [MOOD: ...]
    clean_text = re.sub(r'\[ACTION:.*?\]', '', clean_text, flags=re.IGNORECASE)
    clean_text = re.sub(r'\[MOOD:.*?\]', '', clean_text, flags=re.IGNORECASE)
    
    # 3. Strip unwanted tags like [wave], [execute], etc.
    clean_text = re.sub(r'\[(wave|execute|love|angry|laugh|cry|blush|wink)\]', '', clean_text, flags=re.IGNORECASE)
    
    clean_text = clean_text.strip()
    
    if not clean_text:
        return None

    # Unique temp file
    filename = f"tts_{uuid.uuid4()}.mp3"
    filepath = os.path.join(tempfile.gettempdir(), filename)
    
    try:
        communicate = edge_tts.Communicate(clean_text, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(filepath)
        return filepath
    except Exception as e:
        print(f"[TTS-GEN ERROR] {e}")
        return None

def cleanup_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except:
        pass

@app.post("/tts")
async def tts_endpoint(request: SpeakRequest, background_tasks: BackgroundTasks):
    """Generates TTS audio and returns the file (for client-side playback)."""
    print(f"[TTS-API] Generating audio for: {request.text[:50]}...")
    filepath = await generate_tts_file(request.text)
    if not filepath:
        raise HTTPException(status_code=400, detail="No text provided or generation failed")
    
    background_tasks.add_task(cleanup_file, filepath)
    return FileResponse(filepath, media_type="audio/mpeg", filename="tts.mp3")

@app.post("/speak")
async def speak_endpoint(request: SpeakRequest):
    print(f"[TTS] Manuelle Anforderung: {request.text[:50]}...")
    speak(request.text)
    return {"status": "speaking"}

@app.post("/stop")
async def stop_endpoint():
    global stop_signal, current_tts_process
    print("[BACKEND] Stop-Befehl erhalten!")
    
    # 1. Stop Text Generation
    stop_signal = True
    
    # 2. Stop TTS Process (Server Side)
    if current_tts_process and current_tts_process.poll() is None:
        try:
            current_tts_process.terminate()
            print("[BACKEND] TTS Prozess beendet.")
        except Exception as e:
            print(f"[BACKEND] Fehler beim Beenden von TTS: {e}")
            
    return {"status": "stopped"}

# --- CAMERA ENDPOINTS ---

class CameraConfigRequest(BaseModel):
    id: str
    name: str
    url: str

@app.get("/cameras")
async def get_cameras():
    return camera_manager.get_cameras()

# Duplicate /avatar-check removed to use the smart one below

@app.post("/cameras")
async def add_camera(cam: CameraConfigRequest):
    camera_manager.add_camera(cam.id, cam.name, cam.url)
    return {"status": "added", "cameras": camera_manager.get_cameras()}

@app.delete("/cameras/{cam_id}")
async def remove_camera(cam_id: str):
    camera_manager.remove_camera(cam_id)
    return {"status": "removed", "cameras": camera_manager.get_cameras()}

@app.get("/cameras/{cam_id}/stream")
async def camera_stream(cam_id: str):
    return StreamingResponse(
        camera_manager.generate_mjpeg_stream(cam_id),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

@app.get("/cameras/{cam_id}/snapshot")
async def camera_snapshot_endpoint(cam_id: str):
    path = camera_manager.get_snapshot(cam_id)
    if not path:
        raise HTTPException(status_code=404, detail="Konnte keinen Snapshot erstellen")
    return FileResponse(path)

# --- PHYGITAL ENDPOINTS ---
@app.get("/phygital/state")
async def get_phygital_state():
    if phygital_manager:
        # 1. Legacy Reaction (One-time fetch)
        reaction = phygital_manager.pending_reaction
        if reaction:
            phygital_manager.pending_reaction = None # Clear after fetch
        
        # 2. Broadcast Reaction (Persistent for 15s, Multi-Client)
        broadcast = getattr(phygital_manager, 'broadcast_message', None)
        if broadcast:
            # Check expiry (15 seconds)
            if time.time() - broadcast.get("timestamp", 0) > 15:
                broadcast = None

        return {
            "state": phygital_manager.get_current_state(),
            "temp": phygital_manager.last_temp if hasattr(phygital_manager, 'last_temp') else 0,
            "reaction": reaction,
            "broadcast": broadcast
        }
    return {"state": "neutral", "temp": 0, "reaction": None, "broadcast": None}

# --- YI IOT SCREEN MIRROR ---
@app.get("/stream/yi")
async def stream_yi_app():
    """Streams the Yi IoT Application Window via MJPEG."""
    from window_stream import yi_streamer
    return StreamingResponse(
        yi_streamer.generate_frames(), 
        media_type="multipart/x-mixed-replace;boundary=frame"
    )

def start_listening_bg():
    # Use dynamic path based on current file location
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "models", "vosk-model-small-de-0.15")
    
    try:
        if not os.path.exists(model_path):
            print(f"[WAKEWORD] Modell nicht gefunden unter {model_path}. Deaktiviere Haruko-Ruf.")
            return
        listener = WakeWordListener(model_path)
        # Verbinde den Listener mit der echten Action (trigger_action)
        listener.listen(trigger_action)
    except Exception as e:
        print(f"[WAKEWORD] Lokale Triggerwort-Erkennung deaktiviert: {e}")
        print("[HINWEIS] Das ist kein fataler Fehler. Haruko ist weiterhin über die GUI und das Handy (Mic-Button) steuerbar.")

# Starte den Hintergrund-Listener
threading.Thread(target=start_listening_bg, daemon=True).start()

@app.get("/stats")
async def get_stats():
    try:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        # Basic GPU check via nvidia-smi if available
        gpu = "N/A"
        try:
            gpu_info = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,nounits,noheader"], text=True)
            used, total = gpu_info.strip().split(",")
            gpu = f"{used}MB / {total}MB"
        except:
            pass
        
        return {
            "cpu": cpu,
            "ram": ram,
            "gpu": gpu
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/process_audio")
async def process_audio(file: UploadFile = File(...)):
    print(f"[VOICE] Empfange Audio-Upload: {file.filename}")
    tmp_input = None
    tmp_output = None
    try:
        import tempfile
        
        # Save upload to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(await file.read())
            tmp_input = tmp.name
        
        # Convert to WAV using ffmpeg with explicit parameters for SpeechRecognition
        # -ar 16000: Sample rate 16kHz
        # -ac 1: Mono channel
        tmp_output = tmp_input + ".wav"
        print(f"[VOICE] Konvertiere {tmp_input} zu {tmp_output} (16kHz, Mono)...")
        
        # Check if file is empty
        if os.path.getsize(tmp_input) == 0:
            raise Exception("Hochgeladene Audio-Datei ist leer (0 Bytes).")

        cmd = ["ffmpeg", "-y", "-i", tmp_input, "-ar", "16000", "-ac", "1", tmp_output]
        # Increase log level if needed or capture stderr
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[VOICE] FFmpeg Fehler: {result.stderr}")
            raise Exception(f"FFmpeg Konvertierung fehlgeschlagen. Codec Problem? Log: {result.stderr[:100]}...")
        
        r = sr.Recognizer()
        with sr.AudioFile(tmp_output) as source:
            print("[VOICE] Lese Audio-Datei...")
            audio = r.record(source)
            print("[VOICE] Starte Google STT...")
            text = r.recognize_google(audio, language="de-DE")
        
        print(f"[VOICE] Transkription erfolgreich: '{text}'")
        
        # Clean up
        if os.path.exists(tmp_input): os.unlink(tmp_input)
        if os.path.exists(tmp_output): os.unlink(tmp_output)
        
        # Return only text, let frontend handle the chat flow
        return {"text": text}
    except Exception as e:
        if tmp_input and os.path.exists(tmp_input): os.unlink(tmp_input)
        if tmp_output and os.path.exists(tmp_output): os.unlink(tmp_output)
        print(f"[VOICE] FEHLER bei Audio-Verarbeitung: {e}")
        return {"error": str(e)}

@app.post("/api/vision/analyze")
async def analyze_vision_frame(file: UploadFile = File(...)):
    """
    Receives a camera frame from the mobile client, analyzes it for faces,
    and triggers Haruko's reaction if a known person is found.
    """
    import shutil
    import vision
    
    # print(f"[MOBILE VISION] Empfange Frame: {file.filename}")
    
    # Save to temp
    temp_path = os.path.join("temp_vision", f"mobile_{int(time.time())}.jpg")
    if not os.path.exists("temp_vision"): os.makedirs("temp_vision")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Analyze Faces
        names = vision.analyze_faces(temp_path)
        
        # Reaction Logic
        if names:
            # Update Global Context for LLM (Always, even if unknown)
            global LATEST_VISION_CONTEXT
            
            known_people = [n for n in names if n != "Unknown"]
            
            if known_people:
                person = known_people[0]
                LATEST_VISION_CONTEXT["person"] = person
                print(f"[MOBILE VISION] Bekannte Person erkannt: {person}")
            else:
                # If only unknown people are seen
                if not LATEST_VISION_CONTEXT["person"]: # Don't overwrite a known person with unknown immediately
                     LATEST_VISION_CONTEXT["person"] = "Unknown"
                print("[MOBILE VISION] Unbekannte Person(en) erkannt.")

            LATEST_VISION_CONTEXT["timestamp"] = time.time()
            
            if known_people:
                person = known_people[0]
                # Check Cooldown (Simple in-memory for now)
                # In a real app, use a dict with timestamps
                # For now, we just log it and maybe speak
                # speak(f"Hallo {person}!") 
                
                # We return the names so the Frontend can decide what to do (or Backend triggers speech)
                return {"status": "success", "detected": names, "action": "greet", "person": person}
            else:
                print("[MOBILE VISION] Nur Unbekannte erkannt.")
                return {"status": "success", "detected": names, "action": "alert"}
        
        return {"status": "success", "detected": [], "action": "none"}

    except Exception as e:
        print(f"[MOBILE VISION] Error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        # Cleanup temp file (Permanent delete, NO Recycle Bin)
        try:
             if os.path.exists(temp_path): 
                 os.unlink(temp_path) # os.unlink deletes directly from filesystem
                 # print(f"[DEBUG] Deleted {temp_path}") 
        except: pass

# Cleanup leftovers on startup
def cleanup_temp_vision():
    folder = "temp_vision"
    if os.path.exists(folder):
        print(f"[SYSTEM] Bereinige temporären Ordner: {folder}...")
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"[SYSTEM] Konnte {file_path} nicht löschen: {e}")

# Run cleanup on import/startup
cleanup_temp_vision()

@app.get("/listen")
async def listen_voice():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source, timeout=5, phrase_time_limit=10)
    try:
        # Use google for demo, if local is needed user should install PocketSphinx or Whisper
        text = r.recognize_google(audio, language="de-DE")
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

@app.get("/devices")
async def get_devices():
    """Returns list of available Tuya devices and their status."""
    devices = []
    try:
        # Assuming tuya.devices_cache is a dict: {"Name": "ID"}
        # We don't have live state in cache usually, but we can return the names
        for name, dev_info in tuya.devices_cache.items():
            # Fix: dev_info is the dict, so we access ['id']
            devices.append({"name": name, "id": dev_info.get('id', 'unknown'), "type": "switch"}) # Default to switch
        return devices
    except Exception as e:
        return {"error": str(e)}

@app.post("/execute")
async def execute_command(request: ToolCallRequest):
    print(f"[EXECUTE] Empfange Befehl: {request.command}")
    try:
        # Clean command string (remove outer quotes if LLM adds them)
        raw_cmd = request.command.strip().strip('"').strip("'")
        
        # Check for special tuya command
        if raw_cmd.lower().startswith("tuya_control"):
            # Syntax: tuya_control --device "name" --state "on/off"
            # Robust parsing logic (same as in chat loop)
            # Matches: --device "Name" --state, --device 'Name' --state, --device Name --state
            dev_match = re.search(r'--device\s+["\']?([^"\']+?)["\']?\s+--state', raw_cmd, re.IGNORECASE)
            
            # Fallback if --state is not present or at end
            if not dev_match:
                 dev_match = re.search(r'--device\s+["\']?([^"\']+)["\']?', raw_cmd, re.IGNORECASE)

            state_match = re.search(r'--state\s+["\']?(\w+)["\']?', raw_cmd, re.IGNORECASE)
            
            if dev_match and state_match:
                device = dev_match.group(1).strip()
                state = state_match.group(1).strip()
                print(f"[EXECUTE] Tuya Control: Device='{device}', State='{state}'")
                result_text = tuya.control(device, state)
                print(f"[EXECUTE] Result: {result_text}")
                return {"stdout": result_text, "stderr": "", "status": "success"}
            else:
                 print(f"[EXECUTE] Parse Error for cmd: {raw_cmd}")
                 return {"stdout": "", "stderr": "Fehler: Ungültiges Tuya-Format.", "status": "failed"}

        # Check for launch command
        if raw_cmd.lower().startswith("launch"):
            import pc_control
            app_match = re.search(r'--app\s+["\']?([^"\']+)["\']?', raw_cmd, re.IGNORECASE)
            if app_match:
                app_name = app_match.group(1)
                print(f"[EXECUTE] Launch App: {app_name}")
                result_text = pc_control.launch_app(app_name)
                return {"stdout": result_text, "stderr": "", "status": "success"}
            else:
                return {"stdout": "", "stderr": "Fehler: App-Name fehlt.", "status": "failed"}

        # Caution: Unrestricted access as requests
        print(f"[EXECUTE] Shell Command: {raw_cmd}")
        result = subprocess.run(["powershell", "-Command", raw_cmd], capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
             "status": "success" if result.returncode == 0 else "failed"
        }
    except Exception as e:
        print(f"[EXECUTE] Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/notify")
async def receive_notification(notification: NotificationRequest):
    """
    Empfängt Benachrichtigungen von externen Apps (z.B. via MacroDroid/Tasker).
    Haruko liest diese vor oder reagiert darauf.
    """
    print(f"[NOTIFY] Empfangen von {notification.app}: {notification.message}")
    
    # Text zum Vorlesen
    text_to_speak = f"Nachricht von {notification.app}. "
    if notification.title:
        text_to_speak += f"Von {notification.title}. "
    
    # Kürzen bei zu langen Nachrichten
    msg = notification.message
    if len(msg) > 200:
        msg = msg[:200] + "..."
    text_to_speak += msg
    
    # 1. Server-Side Audio (Direkt am PC)
    speak(text_to_speak)

    # 2. Frontend Broadcast (An alle verbundenen Browser/Tablets)
    if phygital_manager:
        phygital_manager.set_broadcast(text_to_speak)
    
    return {"status": "announced", "text": text_to_speak}

@app.get("/avatar-check")
async def check_avatar():
    """Returns the avatar file to use based on room temp (phygital), time, and weather."""
    try:
        from secretary import secretary_service
        import datetime
        
        # Default
        avatar_file = "avatar.vrm"

        # 0. Check Room Temperature (Phygital) - Highest Priority
        if phygital_manager:
            p_state = phygital_manager.get_current_state()
            if p_state == "cold":
                return {"model": "kalt.vrm", "reason": "room_cold"}
            # If hot, we currently don't have a "bikini" model, so fall through to time/weather or default
        
        # 1. Check Time (After 18:00)
        now = datetime.datetime.now()
        if now.hour >= 18:
            avatar_file = "abend.vrm"
            return {"model": avatar_file, "reason": "time_evening"}

        # 2. Check Weather (Cold < 5°C?)
        # Fetch weather for Berlin (default)
        weather_data = secretary_service.get_weather_data("Berlin")
        if weather_data and weather_data.get("temperature") is not None:
            temp = weather_data["temperature"]
            if temp < 5.0: # Threshold for "cold"
                avatar_file = "kalt.vrm"
                return {"model": avatar_file, "reason": "weather_cold"}
        
        return {"model": avatar_file, "reason": "default"}
        
    except Exception as e:
        print(f"[AVATAR] Error: {e}")
        return {"model": "avatar.vrm", "reason": "error"}

def start_secretary_loop():
    import time
    import secretary
    import random
    
    print("[SECRETARY] Starte Hintergrund-Dienst für Timer, Alarme & Autonomie...")
    
    # Init timestamps
    global last_interaction_time
    last_interaction_time = time.time()
    last_boredom_comment = time.time()
    last_temp_warning = 0
    
    # Idle phrases
    idle_phrases = [
        "Master? Bist du noch da?",
        "Es ist so ruhig hier...",
        "Ich langweile mich ein bisschen.",
        "Soll ich etwas Musik anmachen?",
        "Ich scanne gerade das Netzwerk, alles ruhig.",
        "Hast du vergessen, dass ich hier bin?",
        "Ich rechne gerade Pi aus... bin bei der millionsten Stelle."
    ]

    while True:
        try:
            now = time.time()
            
            # 1. Alarms & Timers
            triggered = secretary.secretary_service.check_alarms()
            for label in triggered:
                print(f"[ALARM] {label} ausgelöst!")
                # Sound alert
                import winsound
                try:
                    winsound.Beep(1000, 500)
                    winsound.Beep(1000, 500)
                    winsound.Beep(1000, 500)
                except: pass
                speak(f"Master, Erinnerung: {label}")
            
            # 2. Autonomous Temperature Check (Phygital)
            # Only warn if > 28°C or < 17°C, max once per 2 hours
            if phygital_manager and (now - last_temp_warning > 7200):
                try:
                    temp = getattr(phygital_manager, 'last_temp', None)
                    if temp and isinstance(temp, (int, float)):
                        comment = ""
                        if temp > 28.0:
                            comments = getattr(phygital_manager, 'sarcastic_comments', {}).get('hot', [])
                            if comments:
                                comment = random.choice(comments) + f" (Aktuell {temp} Grad)"
                            else:
                                comment = f"Puh, es ist ganz schön warm hier. Aktuell {temp} Grad."
                        elif temp < 17.0:
                            comments = getattr(phygital_manager, 'sarcastic_comments', {}).get('cold', [])
                            if comments:
                                comment = random.choice(comments) + f" (Aktuell {temp} Grad)"
                            else:
                                comment = f"Brrr, es wird kalt. Nur noch {temp} Grad."
                        
                        if comment:
                            print(f"[AUTONOMY] Temperatur-Warnung: {comment}")
                            speak(comment)
                            last_temp_warning = now
                except Exception as e:
                    print(f"[AUTONOMY] Temp check failed: {e}")

            # 3. Boredom / Idle Comments
            # Only if:
            # - No interaction for > 3 hours (10800s)
            # - No boredom comment for > 6 hours (21600s)
            # - Daytime (09:00 - 21:00)
            from datetime import datetime
            hour = datetime.now().hour
            is_daytime = 9 <= hour <= 21
            
            if is_daytime and (now - last_interaction_time > 10800) and (now - last_boredom_comment > 21600):
                comment = random.choice(idle_phrases)
                print(f"[AUTONOMY] Langeweile erkannt. Sage: {comment}")
                speak(comment)
                last_boredom_comment = now

            time.sleep(10)
        except Exception as e:
            print(f"[SECRETARY] Loop Error: {e}")
            time.sleep(10)

threading.Thread(target=start_secretary_loop, daemon=True).start()



if __name__ == "__main__":
    import uvicorn
    import time
    
    print("\n" + "="*50)
    print("   HARUKO BACKEND STARTUP")
    print("="*50 + "\n")

    try:
        # Start always with HTTP now, as Vite handles HTTPS proxy
        print("[SYSTEM] Starte Backend auf Port 8000 (HTTP)...")
        print("[SYSTEM] Drücke STRG+C zum Beenden.")
        
        # Robust startup with retries or error logging
        # access_log=False verhindert den "GET /stats"-Spam im Terminal
        uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Backend abgestürzt: {e}")
        print("Bitte Screenshot machen oder Fehler kopieren.")
        input("Drücke ENTER zum Schließen...") # Keep window open