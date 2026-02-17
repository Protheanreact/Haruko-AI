import cv2
import os
import time
import json
import threading
from typing import Dict, Optional

# --- CONFIGURATION ---
# Wir speichern die Kameras in einer JSON Datei, damit sie persistent sind.
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "cameras_config.json")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

class CameraManager:
    def __init__(self):
        self.cameras = self.load_config()
        self._lock = threading.Lock()

    def load_config(self) -> Dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[CAM] Fehler beim Laden der Config: {e}")
                return {}
        return {
            "cam1": {"name": "Wohnzimmer", "url": "rtsp://admin:123456@192.168.1.101:554/stream1"},
            "cam2": {"name": "Garten", "url": "rtsp://admin:123456@192.168.1.102:554/stream1"}
        }

    def save_config(self):
        with self._lock:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cameras, f, indent=4)

    def get_cameras(self):
        return self.cameras

    def add_camera(self, cam_id: str, name: str, url: str):
        self.cameras[cam_id] = {"name": name, "url": url}
        self.save_config()

    def remove_camera(self, cam_id: str):
        if cam_id in self.cameras:
            del self.cameras[cam_id]
            self.save_config()

    def get_snapshot(self, cam_id: str) -> Optional[str]:
        """Holt ein Standbild von einer RTSP Kamera für die KI-Analyse."""
        cam = self.cameras.get(cam_id)
        if not cam:
            print(f"[CAM] Kamera {cam_id} nicht gefunden.")
            return None

        url = cam['url']
        print(f"[CAM] Hole Snapshot von {cam['name']} ({url})...")
        
        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            print(f"[CAM] Fehler: Konnte Stream nicht öffnen: {url}")
            return None

        # Puffer leeren (manche Streams buffern alte Frames)
        for _ in range(2):
            cap.read()
            
        ret, frame = cap.read()
        cap.release()

        if ret:
            filename = f"snapshot_{cam_id}.jpg"
            path = os.path.join(TEMP_DIR, filename)
            cv2.imwrite(path, frame)
            print(f"[CAM] Snapshot gespeichert: {path}")
            return path
        else:
            print("[CAM] Fehler: Konnte Frame nicht lesen.")
            return None

    def generate_mjpeg_stream(self, cam_id: str):
        """Generator für MJPEG Stream (für Frontend Live-View)."""
        cam = self.cameras.get(cam_id)
        if not cam:
            return

        url = cam['url']
        
        # Erstelle ein "Offline" Platzhalter-Bild
        offline_frame = self._create_offline_frame(640, 360, f"Offline: {cam['name']}")
        ret, buffer = cv2.imencode('.jpg', offline_frame)
        offline_bytes = buffer.tobytes()

        cap = cv2.VideoCapture(url)
        
        # Reduziere Frame-Rate für Web-View, um Ressourcen zu sparen
        last_frame_time = 0
        target_fps = 5  # 5 FPS reicht für Überwachung
        
        try:
            while True:
                if not cap.isOpened():
                     # Versuche Reconnect, aber sende zwischenzeitlich Offline-Bild
                     yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + offline_bytes + b'\r\n')
                     time.sleep(2)
                     cap = cv2.VideoCapture(url)
                     continue

                now = time.time()
                if (now - last_frame_time) < (1.0 / target_fps):
                    time.sleep(0.05)
                    continue

                ret, frame = cap.read()
                if not ret:
                    # Stream abgerissen?
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + offline_bytes + b'\r\n')
                    cap.release() 
                    time.sleep(2)
                    cap = cv2.VideoCapture(url)
                    continue

                last_frame_time = now
                
                # Optional: Resize für Performance
                # frame = cv2.resize(frame, (640, 360))
                
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"[CAM] Stream Fehler: {e}")
        finally:
            if cap:
                cap.release()

    def _create_offline_frame(self, width, height, text):
        import numpy as np
        img = np.zeros((height, width, 3), np.uint8)
        # Grau Hintergrund
        img[:] = (50, 50, 50)
        # Text
        font = cv2.FONT_HERSHEY_SIMPLEX
        textsize = cv2.getTextSize(text, font, 1, 2)[0]
        textX = (width - textsize[0]) // 2
        textY = (height + textsize[1]) // 2
        cv2.putText(img, text, (textX, textY), font, 1, (200, 200, 200), 2)
        return img




# Globaler Manager
camera_manager = CameraManager()
