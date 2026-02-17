import tinytuya
import json

# Tuya Credentials from main.py
TUYA_ACCESS_ID = "sx8mpy4n4mhxvv4qrm3n"
TUYA_ACCESS_SECRET = "79125502710b40f78213aef8b678f79f"
TUYA_REGION = "eu"

def check_devices():
    print("Connecting to Tuya Cloud...")
    cloud = tinytuya.Cloud(
        apiRegion=TUYA_REGION, 
        apiKey=TUYA_ACCESS_ID, 
        apiSecret=TUYA_ACCESS_SECRET
    )

    print("Fetching devices...")
    devices = cloud.getdevices()
    
    if not devices:
        print("No devices found in Tuya Cloud.")
        return

    print(f"Found {len(devices)} devices.")
    
    cameras = []
    for dev in devices:
        print(f"\nDevice: {dev.get('name')} (Type: {dev.get('category')})")
        print(f"ID: {dev.get('id')}")
        print(f"IP: {dev.get('ip', 'N/A')}")
        print(f"Local Key: {dev.get('key', 'N/A')}")
        
        # Check if it's a camera (sp or cz is often camera, or category 'sp' is plug, 'cz' is socket. Camera is usually 'sp'?? No. 'sxt' or similar)
        # We print all to be sure.
        if dev.get('category') in ['sp', 'cz']: 
            print("-> Likely a Smart Plug/Socket")
        else:
            print(f"-> Category: {dev.get('category')}")

        if 'camera' in dev.get('name', '').lower() or dev.get('category') in ['sf', 'sxt', 'qj']:
            cameras.append(dev)

    print("\n--- Potential Cameras ---")
    for cam in cameras:
        print(f"Name: {cam.get('name')}")
        print(f"ID: {cam.get('id')}")
        print(f"Suggested RTSP URL: rtsp://admin:admin@{cam.get('ip')}:554/live/ch0")
        print("(Note: Password might be 'admin' or needs to be set in App via ONVIF settings)")

if __name__ == "__main__":
    check_devices()
