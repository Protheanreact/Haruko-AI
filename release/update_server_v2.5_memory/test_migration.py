import os
import json
import sqlite3
from memory_db import MemoryDB, BASE_DIR

def verify_migration():
    print("=== Haruko Memory Migration Verification ===")
    print(f"Base Directory: {BASE_DIR}")
    
    db_path = os.path.join(BASE_DIR, "memory.db")
    json_path = os.path.join(BASE_DIR, "secretary_data.json")
    json_bak_path = os.path.join(BASE_DIR, "secretary_data.json.bak")
    
    # 1. Check DB Existence
    if os.path.exists(db_path):
        print(f"[OK] Database found: {db_path}")
    else:
        print(f"[FAIL] Database NOT found at {db_path}")
        return

    # 2. Check Migration Status
    if os.path.exists(json_bak_path):
        print(f"[OK] Backup file found: {json_bak_path} (Migration likely occurred)")
    elif os.path.exists(json_path):
        print(f"[INFO] JSON file found: {json_path} (Migration pending on next run)")
    else:
        print(f"[INFO] No JSON file found. Assuming fresh install or already cleaned.")

    # 3. Verify Data Content
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Count Facts
        cursor.execute("SELECT COUNT(*) FROM facts")
        fact_count = cursor.fetchone()[0]
        print(f"[DATA] Facts in DB: {fact_count}")
        
        # Count Notes
        cursor.execute("SELECT COUNT(*) FROM notes")
        note_count = cursor.fetchone()[0]
        print(f"[DATA] Notes in DB: {note_count}")
        
        conn.close()
        
        if fact_count > 0 or note_count > 0:
            print("[SUCCESS] Data present in SQLite database.")
        else:
            print("[WARN] Database is empty.")
            
    except Exception as e:
        print(f"[ERROR] Database check failed: {e}")

if __name__ == "__main__":
    verify_migration()
