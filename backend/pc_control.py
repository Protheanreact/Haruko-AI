import os
import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None
import pyautogui
from ctypes import cast, POINTER
try:
    from comtypes import CLSCTX_ALL, CoInitialize
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("[PC_CONTROL] Warnung: 'pycaw' oder 'comtypes' nicht gefunden. Audio-Steuerung deaktiviert.")

import subprocess
import time

# --- AUDIO CONTROL ---
def _get_volume_interface():
    if not AUDIO_AVAILABLE:
        raise ImportError("Audio-Module (pycaw/comtypes) sind nicht installiert.")

    # Ensure COM is initialized for this thread
    try:
        CoInitialize()
    except:
        pass # Already initialized

    device = AudioUtilities.GetSpeakers()
    # Newer pycaw returns an AudioDevice object with direct access to EndpointVolume
    return device.EndpointVolume

def set_volume(level: int):
    """Set master volume to a specific percentage (0-100)."""
    try:
        volume = _get_volume_interface()
        # Convert 0-100 to scalar (0.0 - 1.0)
        scalar = max(0.0, min(1.0, level / 100.0))
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return f"Lautstärke auf {level}% gesetzt."
    except Exception as e:
        return f"Fehler bei Lautstärke-Änderung: {e}"

def change_volume(delta: int):
    """Change volume by delta (e.g. +10 or -10)."""
    try:
        volume = _get_volume_interface()
        current = volume.GetMasterVolumeLevelScalar()
        new_level = max(0.0, min(1.0, current + (delta / 100.0)))
        volume.SetMasterVolumeLevelScalar(new_level, None)
        return f"Lautstärke {'erhöht' if delta > 0 else 'verringert'} (jetzt {int(new_level*100)}%)."
    except Exception as e:
        return f"Fehler bei Lautstärke-Änderung: {e}"

def media_action(action: str):
    """Perform media actions: play_pause, next, prev, mute."""
    action = action.lower()
    try:
        if action in ["play", "pause", "stop", "start"]:
            pyautogui.press("playpause")
            return "Media Play/Pause gedrückt."
        elif action in ["next", "weiter", "skip"]:
            pyautogui.press("nexttrack")
            return "Nächster Titel."
        elif action in ["prev", "zurück", "previous"]:
            pyautogui.press("prevtrack")
            return "Vorheriger Titel."
        elif action in ["mute", "stumm"]:
            pyautogui.press("volumemute")
            return "Stummgeschaltet."
        else:
            return f"Unbekannte Media-Aktion: {action}"
    except Exception as e:
        return f"Fehler bei Media-Aktion: {e}"

def scroll(direction="down"):
    """Scrolls the active window."""
    try:
        if direction in ["down", "runter", "weiter", "next"]:
            # Combine scroll and key for better compatibility (TikTok web uses ArrowDown/PageDown)
            pyautogui.press("pagedown") 
            # pyautogui.scroll(-500) # Optional: Mouse wheel
            return "Habe weiter gescrollt."
        elif direction in ["up", "hoch", "zurück", "prev"]:
            pyautogui.press("pageup")
            # pyautogui.scroll(500)
            return "Habe zurück gescrollt."
        else:
            return "Unbekannte Scroll-Richtung."
    except Exception as e:
        return f"Fehler beim Scrollen: {e}"

# --- ADB / CLIENT REMOTE CONTROL ---
def adb_swipe(x1, y1, x2, y2, duration=300):
    """Sends a swipe command to a connected Android device via ADB."""
    try:
        # Check if adb is in path or use absolute path if needed
        # We assume 'adb' is in PATH after running setup_adb.bat
        cmd = f"adb shell input swipe {x1} {y1} {x2} {y2} {duration}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return "ADB Swipe ausgeführt."
        else:
            return f"ADB Fehler: {result.stderr}"
    except Exception as e:
        return f"ADB Exception: {e}"

def adb_scroll(direction="down"):
    """Simulates scrolling on Android via ADB swipes."""
    # Screen coordinates assumption: 1080x1920 (Portrait) or similar
    # Swipe UP to scroll DOWN content
    if direction in ["down", "runter", "weiter", "next"]:
        return adb_swipe(500, 1500, 500, 500, 300)
    elif direction in ["up", "hoch", "zurück", "prev"]:
        return adb_swipe(500, 500, 500, 1500, 300)
    return "Unbekannte Richtung."

# --- SYSTEM STATS ---ADB / CLIENT REMOTE CONTROL ---
def adb_swipe(x1, y1, x2, y2, duration=300):
    """Sends a swipe command to a connected Android device via ADB."""
    try:
        # Check if adb is in path or use absolute path if needed
        cmd = f"adb shell input swipe {x1} {y1} {x2} {y2} {duration}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return "ADB Swipe ausgeführt."
        else:
            return f"ADB Fehler: {result.stderr}"
    except Exception as e:
        return f"ADB Exception: {e}"

def adb_scroll(direction="down"):
    """Simulates scrolling on Android via ADB swipes."""
    # Screen coordinates assumption: 1080x1920 (Portrait) or similar
    # Swipe UP to scroll DOWN content
    if direction in ["down", "runter", "weiter", "next"]:
        return adb_swipe(500, 1500, 500, 500, 300)
    elif direction in ["up", "hoch", "zurück", "prev"]:
        return adb_swipe(500, 500, 500, 1500, 300)
    return "Unbekannte Richtung."

# --- SYSTEM STATS ---
def get_system_stats_text():
    """Returns a natural language string with current system stats."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        
        gpu_text = ""
        try:
            if GPUtil:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_text = f", GPU Auslastung bei {gpu.load*100:.1f}% und Temperatur {gpu.temperature} Grad"
            else:
                gpu_text = "" # Silent fallback
        except Exception:
            gpu_text = ", GPU-Daten nicht verfügbar"

        return f"CPU läuft auf {cpu_percent}%, RAM ist zu {ram_percent}% gefüllt{gpu_text}."
    except Exception as e:
        return f"Konnte Systemstatus nicht abrufen: {e}"

# --- APP LAUNCHER ---
APP_MAPPING = {
    "spotify": "spotify", # Often in path, or needs full path
    "chrome": "chrome",
    "browser": "chrome",
    "notepad": "notepad",
    "rechner": "calc",
    "cmd": "cmd",
    "explorer": "explorer",
    "cyberpunk": "steam://run/1091500", # Example Steam ID
    "steam": "steam",
    "discord": "discord", # Needs to be in PATH or full path
    "yi": r'"C:\Program Files (x86)\YIIOTHomePCClientIntl\YIIOTHomePCClientIntl.exe"',
    "yi iot": r'"C:\Program Files (x86)\YIIOTHomePCClientIntl\YIIOTHomePCClientIntl.exe"',
}

def launch_app(app_name: str):
    """Launch an application by name or mapping."""
    key = app_name.lower()
    
    # Check mapping
    cmd = APP_MAPPING.get(key, key) # Default to trying the name itself
    
    try:
        if "steam://" in cmd:
             subprocess.Popen(["start", cmd], shell=True)
             return f"Starte Steam App: {key}"
        else:
            # Try running as command
            subprocess.Popen(cmd, shell=True)
            return f"Starte {key}..."
    except Exception as e:
        return f"Fehler beim Starten von {key}: {e}"
