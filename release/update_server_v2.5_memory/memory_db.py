import sqlite3
import json
import os
from datetime import datetime
import threading

# Use paths relative to this file to ensure consistency
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "memory.db")
JSON_FILE = os.path.join(BASE_DIR, "secretary_data.json")

class MemoryDB:
    def __init__(self):
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()
        self._migrate_from_json()

    def _init_db(self):
        """Initialize database schema."""
        with self.lock:
            # Facts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Notes table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Alarms table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS alarms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time REAL,
                    label TEXT,
                    type TEXT,
                    active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Meta table (for key-value storage like last_briefing_date)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            self.conn.commit()

    def _migrate_from_json(self):
        """Migrate data from legacy JSON file if it exists and DB is empty."""
        with self.lock:
            # Check if JSON exists
            if not os.path.exists(JSON_FILE):
                return

            # Check if DB is already populated (to avoid double migration)
            self.cursor.execute("SELECT COUNT(*) FROM facts")
            if self.cursor.fetchone()[0] > 0:
                return
            
            print(f"[MEMORY] Migrating legacy data from {JSON_FILE}...")
            
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Migrate Facts
                for fact in data.get("facts", []):
                    try:
                        self.cursor.execute("INSERT OR IGNORE INTO facts (content) VALUES (?)", (fact,))
                    except: pass
                
                # Migrate Notes
                for note in data.get("notes", []):
                    try:
                        # Handle both string and dict formats from older versions
                        content = note["text"] if isinstance(note, dict) else str(note)
                        created_at = note.get("date") if isinstance(note, dict) else datetime.now().isoformat()
                        self.cursor.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", (content, created_at))
                    except: pass
                
                # Migrate Alarms
                for alarm in data.get("alarms", []):
                    try:
                        self.cursor.execute("INSERT INTO alarms (time, label, type) VALUES (?, ?, ?)", 
                                          (alarm["time"], alarm["label"], alarm.get("type", "alarm")))
                    except: pass
                
                # Migrate Meta (last_briefing_date)
                if "last_briefing_date" in data:
                    self.cursor.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", 
                                      ("last_briefing_date", data["last_briefing_date"]))
                
                self.conn.commit()
                print("[MEMORY] Migration successful. Renaming JSON file.")
                
                # Rename JSON file to backup
                try:
                    os.rename(JSON_FILE, JSON_FILE + ".bak")
                except OSError:
                    pass # Might fail if file is open, but data is safe in DB
                    
            except Exception as e:
                print(f"[MEMORY] Migration failed: {e}")

    # --- Facts Methods ---
    def add_fact(self, text):
        with self.lock:
            try:
                self.cursor.execute("INSERT INTO facts (content) VALUES (?)", (text,))
                self.conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False # Already exists

    def get_facts(self):
        with self.lock:
            self.cursor.execute("SELECT content FROM facts ORDER BY created_at DESC")
            return [row[0] for row in self.cursor.fetchall()]

    def delete_fact(self, text):
        with self.lock:
            self.cursor.execute("DELETE FROM facts WHERE content = ?", (text,))
            changed = self.cursor.rowcount > 0
            self.conn.commit()
            return changed

    def search_memory(self, query, limit=5):
        """Search facts and notes for keywords."""
        with self.lock:
            search_term = f"%{query}%"
            # Search facts
            self.cursor.execute("SELECT content, 'fact' as type, created_at FROM facts WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?", (search_term, limit))
            facts = [{"text": row[0], "type": row[1], "date": row[2]} for row in self.cursor.fetchall()]
            
            # Search notes
            self.cursor.execute("SELECT content, 'note' as type, created_at FROM notes WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?", (search_term, limit))
            notes = [{"text": row[0], "type": row[1], "date": row[2]} for row in self.cursor.fetchall()]
            
            # Combine and sort
            results = facts + notes
            results.sort(key=lambda x: x["date"], reverse=True)
            return results[:limit]

    # --- Notes Methods ---
    def add_note(self, text):
        with self.lock:
            self.cursor.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", (text, datetime.now()))
            self.conn.commit()

    def get_notes(self, limit=5):
        with self.lock:
            self.cursor.execute("SELECT content, created_at FROM notes ORDER BY created_at DESC LIMIT ?", (limit,))
            # Convert back to list of dicts for compatibility
            return [{"text": row[0], "date": row[1]} for row in self.cursor.fetchall()][::-1] # Reverse to show chronological order if needed, but usually newest first is better. Keeping compat.

    # --- Meta Methods ---
    def get_meta(self, key, default=None):
        with self.lock:
            self.cursor.execute("SELECT value FROM meta WHERE key = ?", (key,))
            res = self.cursor.fetchone()
            return res[0] if res else default

    def set_meta(self, key, value):
        with self.lock:
            self.cursor.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()

    # --- Alarm Methods ---
    def add_alarm(self, timestamp, label, type="alarm"):
        with self.lock:
            self.cursor.execute("INSERT INTO alarms (time, label, type) VALUES (?, ?, ?)", (timestamp, label, type))
            self.conn.commit()

    def get_active_alarms(self):
        with self.lock:
            # Get all alarms that haven't triggered yet (future timestamp) 
            # OR logic in check_alarms handles the triggering.
            # Here we just return all for compatibility, but filter by active if we implemented soft delete.
            # For now, mimic json behavior: return list of dicts.
            self.cursor.execute("SELECT time, label, type, id FROM alarms")
            return [{"time": row[0], "label": row[1], "type": row[2], "id": row[3]} for row in self.cursor.fetchall()]

    def remove_alarm(self, alarm_id):
        with self.lock:
            self.cursor.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
            self.conn.commit()

    def update_alarms_list(self, new_alarms_list):
        # This is a bit tricky because the old code replaced the whole list.
        # We'll try to sync or just clear and re-add if the list is short.
        # However, check_alarms usually just removes triggered ones.
        # Better approach: check_alarms logic should move here or use remove_alarm.
        pass

    def close(self):
        self.conn.close()
