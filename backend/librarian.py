import os
import time
import re
import json
import threading
import random
import requests
import google.generativeai as genai
from duckduckgo_search import DDGS
from datetime import datetime, timedelta
import shutil

# Import Database to flag learned topics or log actions
# from memory_db import MemoryDB

class Librarian(threading.Thread):
    def __init__(self, memory_db=None, knowledge_dir="knowledge", check_interval=3600):
        """
        Der Bibliothekar (Librarian) verwaltet Harukos Wissen und führt Self-Correction durch.
        
        Args:
            memory_db: Instanz der MemoryDB (optional, für Logs/Status)
            knowledge_dir: Pfad zum Wissens-Ordner
            check_interval: Wie oft der Loop läuft (in Sekunden, Default: 1h)
        """
        super().__init__()
        self.daemon = True
        self.memory_db = memory_db
        self.knowledge_dir = os.path.join(os.path.dirname(__file__), knowledge_dir)
        self.check_interval = check_interval
        self.running = True
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # Ensure knowledge dir exists
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("[LIBRARIAN] WARNUNG: Kein GEMINI_API_KEY. Bibliothekar ist eingeschränkt (nur Suche, keine Synthese).")
            self.model = None

    def run(self):
        print(f"[LIBRARIAN] Dienst gestartet. Intervall: {self.check_interval}s")
        time.sleep(10) # Initial delay to let system boot
        
        while self.running:
            try:
                print("[LIBRARIAN] Beginne Wartungs-Zyklus...")
                
                # 1. Self-Correction: System Health Check
                self.perform_system_check()
                
                # 2. Knowledge Maintenance (Update old files)
                self.maintain_knowledge()
                
                # 3. Learn new topics (from Wishlist or Random - Placeholder)
                # self.learn_pending_topics()
                
                print(f"[LIBRARIAN] Zyklus beendet. Schlafe {self.check_interval}s.")
            except Exception as e:
                print(f"[LIBRARIAN] Fehler im Loop: {e}")
            
            time.sleep(self.check_interval)

    def stop(self):
        self.running = False

    # --- Knowledge Functions ---

    def clean_html(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        lines = [line.strip() for line in cleantext.splitlines() if line.strip()]
        return "\n".join(lines)

    def search_web(self, query, max_results=3):
        print(f"[LIBRARIAN] Suche nach: '{query}'...")
        results = []
        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=max_results))
                for r in search_results:
                    try:
                        resp = requests.get(r['href'], timeout=5, headers={'User-Agent': 'HarukoBot/1.0'})
                        if resp.status_code == 200:
                            content = self.clean_html(resp.text)
                            results.append(f"Quelle: {r['title']} ({r['href']})\nInhalt:\n{content[:4000]}")
                    except:
                        results.append(f"Quelle: {r['title']} ({r['href']})\nInhalt (Snippet):\n{r['body']}")
        except Exception as e:
            print(f"[LIBRARIAN] Such-Fehler: {e}")
        return results

    def synthesize_knowledge(self, topic, raw_data, old_content=""):
        if not self.model: return "Fehler: Kein LLM verfügbar."
        
        print(f"[LIBRARIAN] Synthetisiere Wissen für '{topic}'...")
        
        prompt = f"""
        Du bist der Bibliothekar des KI-Systems Haruko.
        Deine Aufgabe ist es, Wissen zu aktualisieren und zu korrigieren (Self-Correction).
        
        THEMA: {topic}
        
        NEUE QUELLDATEN (Web):
        {'-'*20}
        {"\n\n".join(raw_data)}
        {'-'*20}
        
        ALTE DATEN (Existierender Eintrag):
        {'-'*20}
        {old_content[:2000] if old_content else "Keine alten Daten."}
        {'-'*20}
        
        AUFGABE:
        Erstelle (oder aktualisiere) einen strukturierten Markdown-Eintrag.
        - Prüfe, ob die alten Daten veraltet oder falsch sind. Wenn ja, korrigiere sie.
        - Integriere neue Fakten.
        - Schreibe auf DEUTSCH.
        - Format: Markdown (Überschriften, Bullets).
        - Am Ende: Eine Sektion "Status", die kurz erklärt, was aktualisiert wurde (Self-Correction Log).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Fehler bei der Generierung: {e}"

    def maintain_knowledge(self):
        """Checks for old files and updates them."""
        try:
            files = [f for f in os.listdir(self.knowledge_dir) if f.endswith(".md")]
            if not files: return

            # Find oldest file
            files_full = [os.path.join(self.knowledge_dir, f) for f in files]
            files_full.sort(key=lambda x: os.path.getmtime(x))
            
            oldest_file = files_full[0]
            age_days = (time.time() - os.path.getmtime(oldest_file)) / 86400
            
            # Update if older than 7 days
            if age_days > 7:
                topic = os.path.basename(oldest_file).replace(".md", "").replace("_", " ")
                print(f"[LIBRARIAN] Datei '{os.path.basename(oldest_file)}' ist {age_days:.1f} Tage alt. Aktualisiere...")
                
                # Read old content
                with open(oldest_file, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                
                # Research
                raw_data = self.search_web(topic)
                if raw_data:
                    new_content = self.synthesize_knowledge(topic, raw_data, old_content)
                    
                    # Save
                    with open(oldest_file, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"[LIBRARIAN] '{topic}' erfolgreich aktualisiert.")
                else:
                    print(f"[LIBRARIAN] Konnte keine neuen Infos zu '{topic}' finden.")
                    # Touch file to reset timestamp so we don't loop on it
                    os.utime(oldest_file, None)
        except Exception as e:
            print(f"[LIBRARIAN] Fehler bei maintain_knowledge: {e}")

    def learn_topic(self, topic):
        """Public method to trigger learning manually."""
        print(f"[LIBRARIAN] Manuelles Lernen angefordert: {topic}")
        raw_data = self.search_web(topic)
        if raw_data:
            content = self.synthesize_knowledge(topic, raw_data)
            filename = f"{topic.replace(' ', '_').lower()}.md"
            filepath = os.path.join(self.knowledge_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Wissen über '{topic}' wurde gespeichert."
        return "Konnte keine Informationen finden."

    # --- System Self-Correction ---

    def perform_system_check(self):
        """Checks basic system health."""
        print("[LIBRARIAN] Führe System-Check durch...")
        
        # 1. Disk Space
        try:
            total, used, free = shutil.disk_usage("C:\\") # Assuming server runs on C or E
            free_gb = free // (2**30)
            if free_gb < 2:
                print(f"[SYSTEM CRITICAL] Wenig Speicherplatz: {free_gb}GB!")
                # Potential Auto-Cleanup here
        except: pass

        # 2. Internet Connectivity
        try:
            requests.get("https://www.google.com", timeout=3)
        except:
            print("[SYSTEM WARNING] Keine Internetverbindung!")
        
        # 3. Memory Usage
        # (Could integrate psutil here)
        pass

