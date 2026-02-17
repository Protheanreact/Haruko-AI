import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from secretary import secretary_service

def test_weather():
    cities = ["Berlin", "München", "NonExistentCity12345"]
    
    print("Starte Wetter-Test...\n")
    
    for city in cities:
        print(f"--- Teste Wetter für: {city} ---")
        try:
            result = secretary_service.get_weather(city)
            print(f"Ergebnis: {result}")
        except Exception as e:
            print(f"Fehler bei {city}: {e}")
        print("-" * 30 + "\n")

if __name__ == "__main__":
    test_weather()
