import mss
import pygetwindow as gw
import numpy as np
import cv2
import time
import threading
from PIL import Image, ImageGrab

class WindowStreamer:
    def __init__(self, window_title_keywords):
        # Allow single string or list of strings
        if isinstance(window_title_keywords, str):
            self.keywords = [window_title_keywords]
        else:
            self.keywords = window_title_keywords
        # self.sct = mss.mss() # Removed MSS for stability
        self.running = False
        
    def get_window_rect(self):
        try:
            # Iterate through all keywords
            for keyword in self.keywords:
                # 1. Try exact match first (Case sensitive)
                windows = gw.getWindowsWithTitle(keyword)
                
                for w in windows:
                    if w.title == keyword:
                        return self._return_rect(w)
                
                # 2. If no exact match, try contains (Case insensitive)
                all_w = gw.getAllTitles()
                for w_title in all_w:
                    if keyword.lower() in w_title.lower():
                        # Exclude "Properties" or "Eigenschaften" windows if possible, 
                        # unless that's the only thing found (unlikely for main app)
                        if "eigenschaften" not in w_title.lower() and "properties" not in w_title.lower():
                            target_win = gw.getWindowsWithTitle(w_title)[0]
                            return self._return_rect(target_win)

            # If nothing found after checking all keywords
            return None
                
        except Exception as e:
            print(f"[STREAM] Window Find Error: {e}")
        return None

    def _return_rect(self, target_win):
        # Optional: Restore if minimized? 
        # if target_win.isMinimized:
        #     target_win.restore()
        return {
            "top": target_win.top, 
            "left": target_win.left, 
            "width": target_win.width, 
            "height": target_win.height
        }

    def generate_frames(self):
        print(f"[STREAM] Starting stream for windows containing '{self.keywords}'")
        # Use ImageGrab (PIL) as fallback
        while True:
            rect = self.get_window_rect()
            
            if not rect:
                # Placeholder if window not found
                blank = np.zeros((480, 640, 3), np.uint8)
                cv2.putText(blank, "Waiting for App...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', blank)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(1)
                continue

            try:
                # Capture with ImageGrab
                # bbox = (left, top, right, bottom)
                left = int(rect["left"])
                top = int(rect["top"])
                right = left + int(rect["width"])
                bottom = top + int(rect["height"])
                
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                
                # Convert PIL to OpenCV (RGB -> BGR)
                img = np.array(screenshot)
                frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                # Limit FPS to ~10
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[STREAM] Capture Error: {e}")
                time.sleep(1)

# Global Instance
yi_streamer = WindowStreamer(["YI IOT", "Yi IoT", "YIIOT", "Yi Home", "ClientIntl"])
