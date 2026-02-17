import cv2
import os
import time
import mss
import numpy as np
import re

# Optional import for face_recognition to avoid crashes if not installed
try:
    import face_recognition
except ImportError:
    face_recognition = None

TEMP_DIR = "temp_vision"
KNOWN_FACES_DIR = "known_faces"

# --- CACHING SYSTEM ---
FACE_CACHE = {
    "encodings": [],
    "names": [],
    "last_loaded": 0
}

if not os.path.exists(TEMP_DIR):
    try:
        os.makedirs(TEMP_DIR)
    except: pass

if not os.path.exists(KNOWN_FACES_DIR):
    try:
        os.makedirs(KNOWN_FACES_DIR)
    except: pass

def capture_webcam(cam_index=0):
    print(f"[VISION] Versuche Zugriff auf Webcam {cam_index}...")
    cap = cv2.VideoCapture(cam_index)
    if not cap.isOpened():
        print(f"[VISION] Fehler: Konnte Kamera {cam_index} nicht öffnen.")
        return None
    
    # Warmup
    for _ in range(5):
        cap.read()
        
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        filename = os.path.join(TEMP_DIR, f"webcam_{int(time.time())}.jpg")
        cv2.imwrite(filename, frame)
        print(f"[VISION] Webcam-Bild gespeichert: {filename}")
        return filename
    else:
        print("[VISION] Konnte keinen Frame lesen.")
        return None

def capture_screen():
    print("[VISION] Erstelle Screenshot...")
    try:
        with mss.mss() as sct:
            # Monitor 1 ist meist der primäre Monitor
            monitor = sct.monitors[1] 
            screenshot = sct.grab(monitor)
            
            # Convert to numpy array
            img = np.array(screenshot)
            
            # MSS returns BGRA, OpenCV needs BGR
            # Check dimensions to be safe
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            filename = os.path.join(TEMP_DIR, f"screen_{int(time.time())}.jpg")
            cv2.imwrite(filename, img)
            print(f"[VISION] Screenshot gespeichert: {filename}")
            return filename
    except Exception as e:
        print(f"[VISION] Screenshot Fehler: {e}")
        return None

def analyze_faces(image_path):
    """
    Analyzes the given image for faces and compares them with known faces.
    Returns a list of recognized names.
    """
    # Fallback to OpenCV if face_recognition is missing
    if not face_recognition:
        # Fallback to OpenCV if face_recognition is not available
        import cv2
        print("[VISION] Fallback zu OpenCV...")
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"[VISION] Fehler: Konnte Bild nicht laden: {image_path}")
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if face_cascade.empty():
                print("[VISION] Fehler: Haar Cascade nicht gefunden.")
                return []
            
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            print(f"[VISION] OpenCV hat {len(faces)} Gesichter gefunden.")
            
            if len(faces) > 0:
                return ["Unknown"] * len(faces)
            return []
        except Exception as e:
            print(f"[VISION] OpenCV Fehler: {e}")
            return []

    if not os.path.exists(KNOWN_FACES_DIR):
        print(f"[VISION] Ordner {KNOWN_FACES_DIR} fehlt.")
        return []

    print(f"[VISION] Analysiere Gesichter in {image_path}...")
    try:
        # Load image
        unknown_image = face_recognition.load_image_file(image_path)
        
        # Detect faces (locations)
        face_locations = face_recognition.face_locations(unknown_image)
        if not face_locations:
            print(f"[VISION] Keine Gesichter gefunden. (Pfad: {image_path})")
            return []

        print(f"[VISION] {len(face_locations)} Gesichter gefunden. Starte Identifizierung...")

        # Encode faces
        unknown_encodings = face_recognition.face_encodings(unknown_image, face_locations)

        recognized_names = []
        
        # --- CACHED LOADING START ---
        global FACE_CACHE
        dir_mtime = os.path.getmtime(KNOWN_FACES_DIR)
        
        # Reload only if directory changed or cache empty
        if dir_mtime > FACE_CACHE["last_loaded"] or not FACE_CACHE["names"]:
            print("[VISION] Cache veraltet oder leer. Lade bekannte Gesichter neu...")
            new_encodings = []
            new_names = []
            
            for filename in os.listdir(KNOWN_FACES_DIR):
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    try:
                        path = os.path.join(KNOWN_FACES_DIR, filename)
                        raw_name = os.path.splitext(filename)[0] 
                        # Normalize name: "Jenny_1" -> "Jenny", "Master_2" -> "Master"
                        name = re.sub(r'[_\-\s]*\d+$', '', raw_name)
                        
                        # print(f"[VISION] Lade Gesicht: {filename} -> Name: {name}")

                        img = face_recognition.load_image_file(path)
                        encs = face_recognition.face_encodings(img)
                        if encs:
                            new_encodings.append(encs[0])
                            new_names.append(name)
                    except Exception as ex:
                        print(f"[VISION] Fehler beim Laden von {filename}: {ex}")
            
            # Update Cache
            FACE_CACHE["encodings"] = new_encodings
            FACE_CACHE["names"] = new_names
            FACE_CACHE["last_loaded"] = dir_mtime
            print(f"[VISION] Cache aktualisiert. {len(new_names)} Gesichter geladen.")
        
        known_encodings = FACE_CACHE["encodings"]
        known_names = FACE_CACHE["names"]
        # --- CACHED LOADING END ---
        
        # Compare
        for unknown_encoding in unknown_encodings:
            matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.6)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
            
            recognized_names.append(name)

        print(f"[VISION] Erkannte Personen: {recognized_names}")
        return recognized_names

    except Exception as e:
        print(f"[VISION] FaceID Fehler: {e}")
        return []

