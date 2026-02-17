import sys
import traceback
import asyncio
import edge_tts
import pygame
import os
import tempfile
import re

async def play_audio_edge(text):
    """Generates audio using edge-tts and plays it via pygame."""
    try:
        # Determine language and voice
        LANGUAGE = os.getenv("LANGUAGE", "DE").upper()
        
        # Voice selection
        # DE: Amala (Young/Anime), Katja, Conrad
        # EN: Ana (Child/Anime-like), Aria (Neutral), Christopher
        if LANGUAGE == "EN":
            VOICE = "en-US-AnaNeural" # Slightly younger, more "anime" potential than Aria
        else:
            VOICE = "de-DE-AmalaNeural"
            
        RATE = "+10%"
        PITCH = "+25Hz"
        
        # Clean text: Remove EXECUTE commands and technical output carefully
        # Do NOT split/cut off the text. Replace commands with empty string.
        clean_text = re.sub(r'EXECUTE:\s*.*?(?=(\n|$))', '', text, flags=re.IGNORECASE)
        clean_text = re.sub(r'\(?t?uya_control.*?(?=(\)|$|\n))', '', clean_text, flags=re.IGNORECASE)
        # Also strip stray --device flags if they remain (e.g. from multi-line hallucinations)
        clean_text = re.sub(r'--device\s+.*?(?=(\n|$))', '', clean_text, flags=re.IGNORECASE)
        
        # Remove emojis and astral plane symbols to prevent TTS reading them
        clean_text = re.sub(r'[^\000-\177]', '', clean_text) # Simple ASCII keep, removes emojis/unicode
        # Better regex for just emojis/symbols if we want to keep German umlauts:
        # But for now, ensuring no emojis are read is priority.
        # Let's use a smarter regex that keeps Umlauts but kills emojis.
        # This regex matches common emoji ranges and symbols
        emoji_pattern = re.compile("["
            u"\U0001f600-\U0001f64f"  # emoticons
            u"\U0001f300-\U0001f5ff"  # symbols & pictographs
            u"\U0001f680-\U0001f6ff"  # transport & map symbols
            u"\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "+]", flags=re.UNICODE)
        clean_text = emoji_pattern.sub(r'', clean_text)

        if not clean_text:
            return

        # Generate MP3 to temp file
        temp_file = os.path.join(tempfile.gettempdir(), f"moltbot_tts_{os.getpid()}.mp3")
        
        communicate = edge_tts.Communicate(clean_text, VOICE, rate=RATE, pitch=PITCH)
        await communicate.save(temp_file)

        # Play with pygame
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()
        
        # Cleanup
        try:
            os.remove(temp_file)
        except:
            pass
            
    except Exception:
        traceback.print_exc()

def speak_now(text):
    asyncio.run(play_audio_edge(text))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = sys.argv[1]
        speak_now(text)
    else:
        # Read from stdin if no args
        text = sys.stdin.read()
        speak_now(text)
