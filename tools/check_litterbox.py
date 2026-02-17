import os
import tinytuya
import json
from dotenv import load_dotenv

# Load env from parent dir
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

def check():
    api_key = os.getenv("TUYA_ACCESS_ID")
    api_secret = os.getenv("TUYA_ACCESS_SECRET")
    region = os.getenv("TUYA_REGION", "eu")
    
    print(f"Connecting to Tuya Cloud ({region})...")
    c = tinytuya.Cloud(apiRegion=region, apiKey=api_key, apiSecret=api_secret)
    
    # ID aus deiner config
    dev_id = "bfb253e97eb7caeaa356zu" 
    
    print(f"Fetching status for {dev_id}...")
    try:
        status = c.getstatus(dev_id)
        print("\n--- RAW STATUS ---")
        print(json.dumps(status, indent=2))
        
        print("\n--- ANALYSE ---")
        if 'result' in status:
            for item in status['result']:
                print(f"Code: {item.get('code')} | Value: {item.get('value')}")
        else:
            print("Kein Ergebnis. ID falsch oder Gerät offline?")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check()