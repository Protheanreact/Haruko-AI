import os
import tinytuya
import json
from dotenv import load_dotenv

# Load env from backend/.env
env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
load_dotenv(env_path)

ACCESS_ID = os.getenv("TUYA_ACCESS_ID")
ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
REGION = os.getenv("TUYA_REGION", "eu")

print(f"Tuya Scanner v1.0")
print(f"ID: {ACCESS_ID}")
print(f"Region: {REGION}")

if not ACCESS_ID or "DEINE" in ACCESS_ID:
    print("Fehler: Bitte trage erst deine Tuya API Daten in backend/.env ein.")
    exit(1)

regions_to_try = [REGION, 'we', 'us']
cloud = None
devices = []

for r in regions_to_try:
    print(f"Prüfe Region: {r}...")
    try:
        c = tinytuya.Cloud(
            apiRegion=r, 
            apiKey=ACCESS_ID, 
            apiSecret=ACCESS_SECRET
        )
        devs = c.getdevices()
        if devs and len(devs) > 0:
            print(f"Treffer in Region {r}! {len(devs)} Geräte gefunden.")
            cloud = c
            devices = devs
            break
    except Exception as e:
        print(f"Fehler in {r}: {e}")

if not cloud:
    print("Keine Geräte gefunden. API-Key oder Region falsch?")
    exit(1)

print("\n--- Geräte Details & Status ---")

# Save Cloud Devices to JSON for inspection
with open("cloud_devices.json", "w", encoding="utf-8") as f:
    json.dump(devices, f, indent=2, ensure_ascii=False)
print("[TUYA] Cloud-Geräte in 'cloud_devices.json' gespeichert.")

for d in devices:
    name = d.get('name')
    dev_id = d.get('id')
    category = d.get('category')
    print(f"\n[Gerät] {name}")
    print(f"  ID: {dev_id}")
    print(f"  Category: {category}")
    print(f"  IP (Cloud): {d.get('ip')}")
    print(f"  Local Key: {d.get('key')}")
    
    # Status abrufen
    try:
        status = cloud.getstatus(dev_id)
        print(f"  Status (DPS): {json.dumps(status, indent=2)}")
    except Exception as e:
        print(f"  Konnte Status nicht lesen: {e}")

print("\n-------------------------------")
print("Suche nach lokalen Geräten im Netzwerk (UDP Scan)...")
try:
    tinytuya.scan()
except:
    print("Scan fehlgeschlagen (evtl. Firewall?)")

print("\n-------------------------------")
print("Bitte kopiere die 'Status (DPS)' Ausgabe für den Temperatursensor und die Heizung.")
