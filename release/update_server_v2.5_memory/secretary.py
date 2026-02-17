import time
import threading
from datetime import datetime, timedelta
import requests
from memory_db import MemoryDB

class Secretary:
    def __init__(self):
        # MemoryDB handles its own locking for DB operations, but we might need one for high-level logic if any
        self.db = MemoryDB()

    def add_note(self, text):
        self.db.add_note(text)
        return "Notiz gespeichert."

    def add_fact(self, text):
        if self.db.add_fact(text):
            return f"Fakt gespeichert: {text}"
        return "Fakt war bereits bekannt."

    def delete_fact(self, text):
        if self.db.delete_fact(text):
            return f"Fakt gelöscht: {text}"
        return "Fakt nicht gefunden."

    def get_facts(self):
        return self.db.get_facts()

    def search_memory(self, query):
        results = self.db.search_memory(query, limit=5)
        if not results:
            return f"Nichts zu '{query}' gefunden."
        
        lines = []
        for r in results:
            type_label = "Fakt" if r["type"] == "fact" else "Notiz"
            lines.append(f"- [{type_label}] {r['text']}")
        return "Gefundene Einträge:\n" + "\n".join(lines)

    def get_last_briefing_date(self):
        return self.db.get_meta("last_briefing_date", "")

    def set_last_briefing_date(self, date_str):
        self.db.set_meta("last_briefing_date", date_str)

    def get_notes(self):
        notes = self.db.get_notes(limit=5)
        if not notes:
            return "Du hast keine Notizen."
        return "Deine letzten Notizen:\n" + "\n".join([f"- {n['text']}" for n in notes])

    def set_timer(self, minutes, label="Timer"):
        target_time = datetime.now() + timedelta(minutes=minutes)
        self.db.add_alarm(target_time.timestamp(), label, "timer")
        return f"Timer für {minutes} Minuten ({label}) gestellt."

    def set_alarm(self, time_str, label="Wecker"):
        # Format HH:MM
        try:
            now = datetime.now()
            target = datetime.strptime(time_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if target < now:
                target += timedelta(days=1)
            
            self.db.add_alarm(target.timestamp(), label, "alarm")
            return f"Wecker auf {time_str} gestellt."
        except ValueError:
            return "Fehler: Zeitformat muss HH:MM sein."

    def check_alarms(self):
        # Returns list of triggered alarms
        triggered = []
        now = datetime.now().timestamp()
        
        # Get all alarms from DB
        alarms = self.db.get_active_alarms()
        
        for alarm in alarms:
            # alarm is dict: {time, label, type, id}
            if alarm["time"] <= now:
                triggered.append(alarm["label"])
                # Remove from DB
                self.db.remove_alarm(alarm["id"])
        
        return triggered

    def get_weather_data(self, city="Berlin"):
        """Returns structured weather data (temp, code) or None on error."""
        try:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
            geo_resp = requests.get(geo_url).json()
            
            if not geo_resp.get("results"):
                return None
                
            location = geo_resp["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            
            # 2. Weather
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
            w_resp = requests.get(w_url).json()
            
            current = w_resp.get("current", {})
            return {
                "temperature": current.get("temperature_2m"),
                "weather_code": current.get("weather_code")
            }
        except Exception as e:
            print(f"Weather Data Error: {e}")
            return None

    def get_weather(self, city="Berlin"):
        # Use Open-Meteo for accurate data
        try:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=de&format=json"
            geo_resp = requests.get(geo_url).json()
            
            if not geo_resp.get("results"):
                # Fallback to wttr.in if city not found
                resp = requests.get(f"https://wttr.in/{city}?format=3&m")
                if resp.status_code == 200:
                    return f"Wetterbericht (wttr.in): {resp.text.strip()}"
                return f"Konnte Stadt '{city}' nicht finden."
                
            location = geo_resp["results"][0]
            lat = location["latitude"]
            lon = location["longitude"]
            name = location["name"]
            country = location.get("country", "")
            
            # 2. Weather
            w_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,apparent_temperature&timezone=auto"
            w_resp = requests.get(w_url).json()
            
            current = w_resp.get("current", {})
            temp = current.get("temperature_2m")
            apparent = current.get("apparent_temperature")
            code = current.get("weather_code")
            
            # WMO Code translation
            condition = "Unbekannt"
            if code == 0: condition = "Klar"
            elif code in [1, 2, 3]: condition = "Bewölkt"
            elif code in [45, 48]: condition = "Nebel"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: condition = "Regen"
            elif code in [71, 73, 75, 77, 85, 86]: condition = "Schnee"
            elif code in [95, 96, 99]: condition = "Gewitter"
            
            return f"Wetter in {name} ({country}): {condition}, {temp}°C (Gefühlt: {apparent}°C)."
            
        except Exception as e:
            print(f"Weather Error: {e}")
            # Last Resort Fallback
            try:
                resp = requests.get(f"https://wttr.in/{city}?format=3&m")
                if resp.status_code == 200:
                    return f"Wetterbericht (Backup): {resp.text.strip()}"
            except:
                pass
            return f"Fehler beim Wetterabruf: {e}"

# Singleton instance
secretary_service = Secretary()
