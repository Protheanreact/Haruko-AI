import os
import sys
import subprocess
import importlib.util
import time
import shutil

# Configuration
REQUIRED_PACKAGES = [
    "fastapi", "uvicorn", "python-multipart", "requests", "ollama", "vosk", 
    "pyaudio", "tinytuya", "pyttsx3", "SpeechRecognition", "psutil", 
    "opencv-python", "pillow", "pyautogui", "pydantic", "python-dotenv", 
    "openai", "aiohttp", "pynput", "pyowm", "ddgs", "python-telegram-bot", 
    "pypdf", "mss", "google-generativeai", "edge-tts", "pygame", "groq", "GPUtil"
]

REQUIRED_MODELS = ["llama3.1", "llava"] # Adjust if needed (e.g. llama3.1:latest)

def print_header(title):
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def run_command(command, description):
    print(f"[CMD] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python_version():
    print_header("1. PYTHON VERSION CHECK")
    v = sys.version_info
    print(f"Current Version: {v.major}.{v.minor}.{v.micro}")
    if v.major == 3 and v.minor >= 10:
        print("✅ Python version is sufficient.")
    else:
        print("⚠️  Warning: Python 3.10+ is recommended.")

def check_and_install_packages():
    print_header("2. DEPENDENCY CHECK & FIX")
    missing = []
    
    # Map package names to import names where they differ
    import_map = {
        "python-multipart": "multipart",
        "opencv-python": "cv2",
        "pillow": "PIL",
        "python-dotenv": "dotenv",
        "SpeechRecognition": "speech_recognition",
        "google-generativeai": "google.generativeai",
        "python-telegram-bot": "telegram",
        "ddgs": "duckduckgo_search" # wait, ddgs package provides 'ddgs' import usually, but let's check
    }

    # Special handling for ddgs which is installed as 'ddgs' but might be imported as 'ddgs'
    # Actually 'ddgs' package provides 'ddgs' module.
    # 'python-multipart' often causes issues, check 'multipart'

    installed_packages = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True).stdout.lower()

    for pkg in REQUIRED_PACKAGES:
        # Simple string check in pip list output (more robust than import check for some packages)
        # Handle package name differences in pip list (usually replacements like _ to -)
        search_name = pkg.lower().replace("_", "-")
        if search_name not in installed_packages:
            missing.append(pkg)
            print(f"❌ Missing: {pkg}")
        else:
            print(f"✅ Found: {pkg}")

    if missing:
        print(f"\nFound {len(missing)} missing packages. Installing...")
        cmd = [sys.executable, "-m", "pip", "install"] + missing
        try:
            subprocess.check_call(cmd)
            print("✅ All missing packages installed successfully.")
        except subprocess.CalledProcessError:
            print("❌ Failed to install some packages. Please run 'pip install -r requirements.txt' manually.")
    else:
        print("\n✅ All dependencies are installed.")

def check_ollama():
    print_header("3. OLLAMA CHECK & FIX")
    
    # 1. Check if Ollama is running
    is_running, _ = run_command("ollama list", "Checking Ollama Service")
    if not is_running:
        print("❌ Ollama seems NOT to be running.")
        print("   Attempting to start Ollama app (Windows)...")
        try:
            # Try launching ollama app - path might vary
            subprocess.Popen("ollama app", shell=True)
            print("   Waiting 10s for Ollama to start...")
            time.sleep(10)
        except:
            print("⚠️  Could not auto-start Ollama. Please start it manually.")
    else:
        print("✅ Ollama Service is running.")

    # 2. Check Models
    success, output = run_command("ollama list", "Listing Models")
    if success:
        existing_models = output.lower()
        for model in REQUIRED_MODELS:
            if model in existing_models:
                print(f"✅ Model found: {model}")
            else:
                print(f"❌ Model missing: {model}")
                print(f"   Downloading {model} (this may take a while)...")
                # Stream the pull output
                try:
                    subprocess.run(f"ollama pull {model}", shell=True, check=True)
                    print(f"✅ Model {model} downloaded.")
                except:
                    print(f"❌ Failed to download {model}.")

def check_env_file():
    print_header("4. ENVIRONMENT (.env) CHECK")
    if os.path.exists(".env"):
        print("✅ .env file found.")
        
        # Check critical keys
        with open(".env", "r", encoding="utf-8") as f:
            content = f.read()
        
        keys_to_check = ["GROQ_API_KEY", "GEMINI_API_KEY", "TELEGRAM_TOKEN"]
        for k in keys_to_check:
            if f"{k}=" in content and not f"{k}=\n" in content: # Crude check if not empty
                print(f"✅ Key present: {k}")
            else:
                print(f"⚠️  Key MISSING or EMPTY: {k}")
    else:
        print("❌ .env file NOT found!")
        print("   Creating .env template...")
        with open(".env", "w", encoding="utf-8") as f:
            f.write("GROQ_API_KEY=\nGEMINI_API_KEY=\nTELEGRAM_TOKEN=\nOLLAMA_MODEL=llama3.1:latest\n")
        print("   Created .env. PLEASE FILL IT IN!")

def test_api_connections():
    print_header("5. API CONNECTION TEST")
    
    # Load env vars
    from dotenv import load_dotenv
    load_dotenv()
    
    # Groq Test
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print("Testing Groq API...")
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            client.chat.completions.create(
                messages=[{"role": "user", "content": "hi"}],
                model="llama-3.3-70b-versatile" # Use a valid model
            )
            print("✅ Groq Connection SUCCESS")
        except Exception as e:
            print(f"❌ Groq Connection FAILED: {e}")
            if "model" in str(e).lower():
                 print("   (Might be an invalid model name in test, but connection likely worked)")
    else:
        print("⚠️  Skipping Groq Test (No Key)")

    # Gemini Test
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_FREE")
    if gemini_key:
        print("Testing Gemini API...")
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            model.generate_content("hi")
            print("✅ Gemini Connection SUCCESS")
        except Exception as e:
            print(f"❌ Gemini Connection FAILED: {e}")
    else:
        print("⚠️  Skipping Gemini Test (No Key)")

if __name__ == "__main__":
    print("STARTING SERVER DIAGNOSTICS & AUTO-FIX")
    
    check_python_version()
    check_and_install_packages()
    check_env_file() # Check env before loading it in API test
    check_ollama()
    test_api_connections()
    
    print_header("DIAGNOSTICS COMPLETE")
    print("If all checks passed (✅), you can start the backend with 'python main.py'.")
    input("Press Enter to exit...")
