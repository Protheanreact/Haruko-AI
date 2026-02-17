import os
from dotenv import load_dotenv
from groq import Groq

# Load .env
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Fehler: Kein GROQ_API_KEY gefunden!")
    exit(1)

print(f"Teste Groq mit Key: {api_key[:10]}...")

try:
    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Antworte kurz auf Deutsch: Wer bist du?",
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    print("\nAntwort von Groq:")
    print(chat_completion.choices[0].message.content)
    print("\nTest erfolgreich!")

except Exception as e:
    print(f"\nFehler beim Test: {e}")
