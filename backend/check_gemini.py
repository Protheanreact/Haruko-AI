import google.generativeai as genai
import os

# Use the key from main.py
GEMINI_API_KEY = "AIzaSyC4g1HBYOzE76pAz1xU8yt2trQioGmPwzg"

genai.configure(api_key=GEMINI_API_KEY)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")