import time
import threading
from datetime import datetime, timedelta
import requests
import os
from memory_db import MemoryDB

# Sprache laden (Standard: DE)
LANGUAGE = os.getenv("LANGUAGE", "DE").upper()

class Secretary:
    def __init__(self):
        # MemoryDB handles its own locking for DB operations, but we might need one for high-level logic if any
        self.db = MemoryDB()

    def _msg(self, key, **kwargs):
        """Simple localization helper"""
        msgs = {
            "note_saved": {
                "DE": "Notiz gespeichert.",
                "EN": "Note saved."
            },
            "fact_saved": {
                "DE": "Fakt gespeichert: {text}",
                "EN": "Fact saved: {text}"
            },
            "fact_known": {
                "DE": "Fakt war bereits bekannt.",
                "EN": "Fact was already known."
            },
            "fact_deleted": {
                "DE": "Fakt gelöscht: {text}",
                "EN": "Fact deleted: {text}"
            },
            "fact_not_found": {
                "DE": "Fakt nicht gefunden.",
                "EN": "Fact not found."
            },
            "nothing_found": {
                "DE": "Nichts zu '{query}' gefunden.",
                "EN": "Nothing found for '{query}'."
            },
            "found_entries": {
                "DE": "Gefundene Einträge:\n",
                "EN": "Found entries:\n"
            },
            "no_notes": {
                "DE": "Du hast keine Notizen.",
                "EN": "You have no notes."
            },
            "last_notes": {
                "DE": "Deine letzten Notizen:\n",
                "EN": "Your last notes:\n"
            },
            "timer_set": {
                "DE": "Timer für {minutes} Minuten ({label}) gestellt.",
                "EN": "Timer set for {minutes} minutes ({label})."
            },
            "alarm_set": {
                "DE": "Wecker auf {time_str} gestellt.",
                "EN": "Alarm set for {time_str}."
            },
            "time_format_error": {
                "DE": "Fehler: Zeitformat muss HH:MM sein.",
                "EN": "Error: Time format must be HH:MM."
            },
            "location_set": {
                "DE": "Standort auf '{city}' gesetzt.",
                "EN": "Location set to '{city}'."
            },
            "weather_report": {
                "DE": "Wetterbericht (wttr.in): {text}",
                "EN": "Weather report (wttr.in): {text}"
            },
            "city_not_found": {
                "DE": "Konnte Stadt '{city}' nicht finden.",
                "EN": "Could not find city '{city}'."
            },
            "weather_condition": {
                "DE": "Wetter in {name} ({country}): {condition}, {temp}°C (Gefühlt: {apparent}°C).",
                "EN": "Weather in {name} ({country}): {condition}, {temp}°C (Feels like: {apparent}°C)."
            },
            "weather_error": {
                "DE": "Fehler beim Wetterabruf: {e}",
                "EN": "Error fetching weather: {e}"
            },
            "weather_backup": {
                "DE": "Wetterbericht (Backup): {text}",
                "EN": "Weather report (backup): {text}"
            }
        }
        
        template = msgs.get(key, {}).get(LANGUAGE, msgs.get(key, {}).get("DE", ""))
        return template.format(**kwargs)

    def _translate_condition(self, code):
        """Translates WMO weather codes"""
        if LANGUAGE == "EN":
            if code == 0: return "Clear"
            elif code in [1, 2, 3]: return "Cloudy"
            elif code in [45, 48]: return "Fog"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "Rain"
            elif code in [71, 73, 75, 77, 85, 86]: return "Snow"
            elif code in [95, 96, 99]: return "Thunderstorm"
            return "Unknown"
        else: # DE
            if code == 0: return "Klar"
            elif code in [1, 2, 3]: return "Bewölkt"
            elif code in [45, 48]: return "Nebel"
            elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]: return "Regen"
            elif code in [71, 73, 75, 77, 85, 86]: return "Schnee"
            elif code in [95, 96, 99]: return "Gewitter"
            return "Unbekannt"

    def add_note(self, text):
        self.db.add_note(text)
        return self._msg("note_saved")

    def add_fact(self, text):
        if self.db.add_fact(text):
            return self._msg("fact_saved", text=text)
        return self._msg("fact_known")

    def delete_fact(self, text):
        if self.db.delete_fact(text):
            return self._msg("fact_deleted", text=text)
        return self._msg("fact_not_found")

    def replace_all_facts(self, new_facts):
        if self.db.replace_facts(new_facts):
            return True
        return False

    def get_facts(self):
        return self.db.get_facts()

    def search_memory(self, query):
        results = self.db.search_memory(query, limit=5)
        if not results:
            return self._msg("nothing_found", query=query)
        
        lines = []
        for r in results:
            type_label = "Fakt" if r["type"] == "fact" else "Notiz"
            if LANGUAGE == "EN":
                type_label = "Fact" if r["type"] == "fact" else "Note"
            lines.append(f"- [{type_label}] {r['text']}")
        return self._msg("found_entries") + "\n".join(lines)

    def get_last_briefing_date(self):
        return self.db.get_meta("last_briefing_date", "")

    def set_last_briefing_date(self, date_str):
        self.db.set_meta("last_briefing_date", date_str)

    def get_notes(self):
        notes = self.db.get_notes(limit=5)
        if not notes:
            return self._msg("no_notes")
        return self._msg("last_notes") + "\n".join([f"- {n['text']}" for n in notes])

    def set_timer(self, minutes, label="Timer"):
        target_time = datetime.now() + timedelta(minutes=minutes)
        self.db.add_alarm(target_time.timestamp(), label, "timer")
        return self._msg("timer_set", minutes=minutes, label=label)

    def set_alarm(self, time_str, label="Wecker"):
        # Format HH:MM
        if LANGUAGE == "EN" and label == "Wecker": label = "Alarm"
        
        try:
            now = datetime.now()
            target = datetime.strptime(time_str, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if target < now:
                target += timedelta(days=1)
            
            self.db.add_alarm(target.timestamp(), label, "alarm")
            return self._msg("alarm_set", time_str=time_str)
        except ValueError:
            return self._msg("time_format_error")

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
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language={LANGUAGE.lower()}&format=json"
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

    def get_user_location(self):
        return self.db.get_meta("user_location", "Berlin")

    def set_user_location(self, city):
        self.db.set_meta("user_location", city)
        return self._msg("location_set", city=city)

    def get_weather(self, city=None):
        # Use stored location if no city provided
        if not city:
            city = self.get_user_location()
            
        # Use Open-Meteo for accurate data
        try:
            # 1. Geocoding
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language={LANGUAGE.lower()}&format=json"
            geo_resp = requests.get(geo_url).json()
            
            if not geo_resp.get("results"):
                # Fallback to wttr.in if city not found
                resp = requests.get(f"https://wttr.in/{city}?format=3&m")
                if resp.status_code == 200:
                    return self._msg("weather_report", text=resp.text.strip())
                return self._msg("city_not_found", city=city)
                
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
            
            condition = self._translate_condition(code)
            
            return self._msg("weather_condition", name=name, country=country, condition=condition, temp=temp, apparent=apparent)
            
        except Exception as e:
            print(f"Weather Error: {e}")
            # Last Resort Fallback
            try:
                resp = requests.get(f"https://wttr.in/{city}?format=3&m")
                if resp.status_code == 200:
                    return self._msg("weather_backup", text=resp.text.strip())
            except:
                pass
            return self._msg("weather_error", e=e)

# Singleton instance
secretary_service = Secretary()
