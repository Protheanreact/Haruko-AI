import sys
import os
import time

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from phygital import PhygitalManager

def test():
    print("Initializing PhygitalManager...")
    pm = PhygitalManager()
    
    print("Checking sensors manually...")
    pm.check_sensors()
    
    print("\nLitter Data:", pm.litter_data)
    print("Last Temp:", pm.last_temp)
    
    summary = pm.get_home_status_summary()
    print("\nSummary Output (Das 'sieht' Haruko):")
    print(f"'{summary}'")

if __name__ == "__main__":
    test()