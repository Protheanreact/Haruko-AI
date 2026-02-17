import google.generativeai as genai
import os

key = "AIzaSyD4VJHhdR9VVd9_SwKq_3rkVfewF4vAyvI"
print(f"Testing Key: {key[:10]}...")

try:
    genai.configure(api_key=key)
    # Test explicitly with gemini-1.5-flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Test. Antworte kurz mit 'OK'.")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
