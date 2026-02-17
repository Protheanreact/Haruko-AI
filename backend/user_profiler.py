import json
import os
import google.generativeai as genai
from datetime import datetime

class UserProfiler:
    def __init__(self, memory_db):
        self.db = memory_db
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    def analyze_and_update(self, face_id, user_input, assistant_response):
        """
        Analysiert die Interaktion und aktualisiert das User-Profil im Hintergrund.
        Sollte idealerweise async oder in einem Thread laufen.
        """
        if not self.model: return

        try:
            # Holen des aktuellen Profils
            profile = self.db.get_user_profile(face_id)
            current_attrs = profile["attributes"] if profile else {}
            name = profile["name"] if profile else "Unknown"

            # LLM Prompt zur Analyse
            prompt = f"""
            Analysiere diese Interaktion zwischen User '{name}' und KI Haruko.
            Extrahiere neue Fakten, Vorlieben oder Persönlichkeitsmerkmale des Users.
            
            AKTUELLES PROFIL:
            {json.dumps(current_attrs, indent=2)}
            
            INTERAKTION:
            User: "{user_input}"
            Haruko: "{assistant_response}"
            
            AUFGABE:
            Gib ein JSON zurück, das NUR neue oder geänderte Attribute enthält. 
            Wenn nichts Neues gelernt wurde, gib {{}} zurück.
            Beispiele für Attribute: "lieblingsfarbe", "hobby", "stimmung", "beziehungsstatus", "wohnort".
            
            JSON OUTPUT ONLY:
            """
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean JSON (remove markdown code blocks if any)
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                if text.endswith("```"):
                    text = text.rsplit("\n", 1)[0]
            
            new_data = json.loads(text)
            
            if new_data:
                print(f"[PROFILER] Update für {name} ({face_id}): {new_data}")
                self.db.update_user_profile(face_id, attributes=new_data)
                
        except Exception as e:
            print(f"[PROFILER] Fehler bei Analyse: {e}")

    async def async_analyze(self, face_id, user_input, assistant_response):
        """Wrapper für asynchrone Ausführung (wenn nötig)"""
        # Da LLM Calls blockieren können, ist Threading hier oft besser als reines Async wenn der LLM-Client nicht async ist.
        # Google GenAI Python SDK ist sync (blocking).
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.analyze_and_update, face_id, user_input, assistant_response)
