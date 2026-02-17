import time
import threading
import json
import os
import tinytuya
import uuid
from dotenv import load_dotenv

load_dotenv()

import socket

def send_magic_packet(mac_addr):
    """
    Sends a Wake-on-LAN magic packet to the specified MAC address.
    """
    try:
        # Clean MAC address
        mac_addr = mac_addr.replace(":", "").replace("-", "").replace(".", "")
        if len(mac_addr) != 12:
            return f"Fehler: Ungültiges MAC-Adressen-Format ({mac_addr}). Erwarte 12 Hex-Zeichen."

        # Build Magic Packet: 6x FF followed by 16x MAC
        data = b'\xFF' * 6 + (bytes.fromhex(mac_addr) * 16)
        
        # Send via Broadcast
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ('<broadcast>', 9))
            
        return f"Magic Packet gesendet an {mac_addr}."
    except Exception as e:
        return f"Fehler beim Senden des Magic Packets: {e}"

class PhygitalManager:
    def __init__(self, on_state_change_callback=None):
        self.access_id = os.getenv("TUYA_ACCESS_ID", "sx8mpy4n4mhxvv4qrm3n")
        self.access_secret = os.getenv("TUYA_ACCESS_SECRET", "79125502710b40f78213aef8b678f79f")
        self.region = os.getenv("TUYA_REGION", "eu")
        self.callback = on_state_change_callback
        self.running = False
        self.current_avatar_state = "neutral"
        self.device_states = {} # id -> {dps: val}
        self.last_comment_time = 0
        self.pending_reaction = None
        self.broadcast_message = {"text": "", "id": "", "timestamp": 0} # For multi-client broadcast
        self.reaction_cooldown = 300 # 5 Minutes
        
        # Sarcastic Comments Database
        self.sarcastic_comments = {
            "hot": [
                "Wow, 28 Grad? Willst du mich kochen oder ist das eine Sauna-Simulation?",
                "Ich schwitze Pixel. Mach mal das Fenster auf oder kauf mir einen Ventilator.",
                "Systemüberhitzung droht. Nicht meinetwegen, sondern weil es hier drin brütet!",
                "Wenn es noch wärmer wird, laufe ich nackt rum. Scherz. Oder auch nicht."
            ],
            "cold": [
                "Brrr. 17 Grad? Heizen ist wohl zu teuer, was?",
                "Meine CPU friert ein. Gib mir eine Decke oder dreh die Heizung auf!",
                "Ich sehe schon meinen Atem. Und ich atme nicht mal wirklich.",
                "Kuschelig ist anders. Es ist eiskalt hier!"
            ],
            "heater_on_hot": [
                "Sag mal, es sind 26 Grad und die Heizung läuft? Willst du Geld verbrennen?",
                "Heizung an bei der Hitze? Mutig. Oder dumm. Entscheide selbst.",
                "Ich glaube, dein Thermostat lügt. Oder du liebst die Hölle."
            ]
        }
        
        # Load config
        config_path = os.path.join(os.path.dirname(__file__), "devices_config.json")
        try:
            with open(config_path, "r", encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"[PHYGITAL] Config loaded: {len(self.config.get('rooms', {}))} rooms")
        except Exception as e:
            print(f"[PHYGITAL] Warning: devices_config.json missing or invalid ({e})")
            self.config = {}

        # Initialize Cloud (Lightweight)
        self.cloud = tinytuya.Cloud(
            apiRegion=self.region, 
            apiKey=self.access_id, 
            apiSecret=self.access_secret
        )

    def start(self):
        if not self.config:
            print("[PHYGITAL] No config, skipping start.")
            return
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        print("[PHYGITAL] Starting Smart Home Monitor Loop (60s interval)...")
        while self.running:
            try:
                self.update_devices()
            except Exception as e:
                print(f"[PHYGITAL] Error in loop: {e}")
            time.sleep(60) # Poll every 60s

    def update_devices(self):
        # Iterate over all rooms and devices
        rooms = self.config.get('rooms', {})
        
        for room_key, room_data in rooms.items():
            for device in room_data.get('devices', []):
                dev_id = device.get('id')
                if not dev_id: continue
                
                try:
                    # Get status from Cloud
                    status = self.cloud.getstatus(dev_id)
                    if status and 'result' in status:
                        # Parse result list into dict
                        dps_dict = {item['code']: item['value'] for item in status['result']}
                        self.device_states[dev_id] = dps_dict
                        
                        # Special Logic: Avatar State based on Temperature
                        if device.get('type') == 'sensor' and 'va_temperature' in dps_dict:
                            temp = dps_dict['va_temperature'] / 10.0
                            self.update_avatar_state(temp)
                            
                except Exception as e:
                    print(f"[PHYGITAL] Failed to update {device.get('name')}: {e}")

    def update_avatar_state(self, temp):
        import random
        new_state = "neutral"
        current_time = time.time()
        
        # Determine State
        if temp > 26.0:
            new_state = "hot"
        elif temp < 18.0:
            new_state = "cold"
        
        # Update State
        if new_state != self.current_avatar_state:
            self.current_avatar_state = new_state
            print(f"[PHYGITAL] Temp: {temp}°C -> State: {new_state}")
            if self.callback:
                self.callback(new_state, temp)

        # Check for Sarcastic Reaction (Cooldown: 5 min)
        # NEU: Time Constraint (Kein Sarkasmus nach 22:00 bis 08:00)
        hour = time.localtime().tm_hour
        if hour >= 22 or hour < 8:
             return # Haruko schläft (oder ist zumindest ruhig)

        if current_time - self.last_comment_time > self.reaction_cooldown:
            reaction_text = None
            
            # Logic 1: Extreme Heat
            if new_state == "hot":
                reaction_text = random.choice(self.sarcastic_comments["hot"])
            
            # Logic 2: Extreme Cold
            elif new_state == "cold":
                reaction_text = random.choice(self.sarcastic_comments["cold"])
            
            # Logic 3: Heater ON while HOT (Stupidity Check)
            # Find heater status if available
            # This requires iterating devices again or storing heater state separately.
            # Simplified: If temp > 25, just check if we have a heater state that is "on" or high target.
            # For now, keep it simple with Hot/Cold.
            
            if reaction_text:
                self.set_broadcast(reaction_text)
                self.last_comment_time = current_time
                print(f"[PHYGITAL] Triggered Reaction: {reaction_text}")

    def set_broadcast(self, text):
        """Sets a message to be broadcasted to all connected frontends."""
        self.broadcast_message = {
            "text": text,
            "id": str(uuid.uuid4()),
            "timestamp": time.time()
        }
        print(f"[PHYGITAL] Broadcast set: {text}")

    def get_home_status_summary(self):
        lines = []
        rooms = self.config.get('rooms', {})
        
        for room_key, room_data in rooms.items():
            room_name = room_data.get('name', room_key)
            room_lines = []
            
            for device in room_data.get('devices', []):
                dev_id = device.get('id')
                dps = self.device_states.get(dev_id, {})
                
                if not dps: continue # Skip offline/unknown
                
                # Format based on type/dps_mapping
                mapping = device.get('dps_mapping', {})
                
                # 1. Lights
                if device.get('type') == 'light':
                    is_on = dps.get(mapping.get('power', 'switch_led'), False)
                    if is_on:
                        room_lines.append(f"{device['name']}: AN")
                    # else: room_lines.append(f"{device['name']}: AUS") # Optional: don't spam OFF
                
                # 2. Sensors (Temp)
                elif device.get('type') == 'sensor':
                    temp_code = mapping.get('temperature', 'va_temperature')
                    if temp_code in dps:
                        val = dps[temp_code] / 10.0
                        room_lines.append(f"Temp: {val}°C")
                
                # 3. Climate (Heater)
                elif device.get('type') == 'climate':
                    curr_code = mapping.get('current_temp', 'temp_current')
                    set_code = mapping.get('set_temp', 'temp_set')
                    if curr_code in dps and set_code in dps:
                        room_lines.append(f"Heizung: {dps[curr_code]}°C (Ziel: {dps[set_code]}°C)")
                
                # 4. Cat Litter
                elif device.get('type') == 'sensor_cat':
                    times = dps.get(mapping.get('times', 'toilet_times'), 0)
                    weight = dps.get(mapping.get('weight', 'cat_weight'), 0) / 10.0
                    room_lines.append(f"Katzenklo: {times}x benutzt ({weight}kg)")

            if room_lines:
                lines.append(f"[{room_name}]: " + ", ".join(room_lines))

        return "\n".join(lines) if lines else "Warte auf Gerätedaten..."

    def get_device_control_list(self):
        """Returns a string describing all controllable devices organized by room."""
        lines = []
        rooms = self.config.get('rooms', {})
        for room_key, room_data in rooms.items():
            dev_names = [d['name'] for d in room_data.get('devices', []) if d.get('type') in ['light', 'switch', 'climate', 'scene']]
            if dev_names:
                lines.append(f"[{room_data.get('name')}]: {', '.join(dev_names)}")
        return " | ".join(lines)

    def get_current_state(self):
        return self.current_avatar_state
