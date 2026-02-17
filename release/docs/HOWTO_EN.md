# User Guide (How-To)

## 1. Starting the System
After installation (see Setup Guide):
1.  Start the backend (e.g., via `start_all.bat` or manually).
2.  Open a browser on your PC, tablet, or smartphone.
3.  Navigate to `https://<SERVER-IP>:5173`.
    - *Note*: Accept the security warning (due to self-signed certificate).

## 2. Using Voice Control
- Click the **Microphone Icon** at the bottom of the chat.
- If you have multiple microphones, select the desired one from the dropdown menu (appears next to the icon).
- Speak your command (e.g., "What is the weather like?").
- Click the icon again to stop recording.

## 3. Smart Home Control
- Switch to the **Smart Home** tab in the top right (or via the bottom menu on mobile).
- You will see a list of your Tuya devices.
- Click **ON** or **OFF** to toggle devices.
- Alternatively via voice: "Turn on the living room light."

## 4. Avatars & Weather
- The avatar adapts automatically:
  - **Default**: Daytime, normal weather.
  - **Cold (< 5°C)**: The avatar dresses warmly (loads `kalt.vrm`).
  - **Evening (> 18:00)**: The avatar switches to evening mode (loads `abend.vrm`).
- The weather is automatically determined based on your location.

## 5. Mobile & Tablet Control (New in v2.5)
If you use Haruko on a smartphone or tablet:
- **Interface**: The top bar is hidden to save space. Use the **Apps Button** (bottom left next to chat input) to access Home, Cameras, or Settings.
- **Back Button**: In full-screen views (Home/Cameras), a floating back button (bottom left) returns you to the chat.
- **Scrolling**: Say "Scroll down" to scroll the chat interface.

## 6. Tablet Remote Control (ADB)
Haruko can control your Android tablet (e.g., for TikTok or reading) if configured:
1.  **Setup**: Run `setup_adb.bat` on your PC and follow the pairing instructions on your tablet (Developer Options > Wireless Debugging).
2.  **Usage**: Say "Scroll down on the tablet" or "Next video".
3.  **Mechanism**: Haruko simulates swipe gestures on the connected device.

## 7. Self-Learning (New in v2.7)
Haruko can now acquire knowledge autonomously:
- **Learning Command**: Say e.g., "Teach me about quantum physics" or "Research how to make sushi".
- **Process**: Haruko starts research, creates a guide, and saves it.
- **Retrieval**: Later you can ask "How do I make sushi?" and Haruko uses the stored knowledge.

## 8. Network Control (WoL)
Haruko can wake up PCs in the network:
- **Prerequisite**: The PC must support Wake-on-LAN (WoL) and have it enabled in BIOS.
- **Command**: "Wake up the PC with MAC address AA:BB:CC:DD:EE:FF".
- **Scanner**: "Scan the network" to find available devices.

## 9. WhatsApp Integration (Local Bridge)
Haruko can chat with you via WhatsApp using a local bridge on the server:

- Login:
  - Run `start_haruko_windows.bat` on the server.
  - A console window "Haruko WhatsApp" appears with a QR code.
  - Scan the QR code in WhatsApp under Linked Devices.
- Who may give commands?
  - The configured master number always has full access.
  - Other users can send commands by prefixing a password, e.g. `PASSWORD: turn on the lights`.
- Usage:
  - Talk to Haruko in a dedicated chat or group (for example "Haruko").
  - In normal chats you can use prefixes like `/Haruko` to address her explicitly.

## 10. Changing Language (German -> English)
Haruko is configured for German by default. To switch to English, you need to edit 3 files:

1.  **Personality (Brain)**:
    - Open `backend/personality.py`.
    - Translate the `SYSTEM_PROMPT` to English.
    - **Important**: Remove the line `SPRACHE: Du antwortest AUSSCHLIESSLICH auf DEUTSCH.`

2.  **Voice (TTS)**:
    - Open `backend/tts_cli.py`.
    - Change `VOICE = "de-DE-AmalaNeural"` to an English voice like `"en-US-AriaNeural"` or `"en-US-JennyNeural"`.

3.  **Speech Recognition (Wakeword)**:
    - Open `frontend/src/App.tsx`.
    - Search for `recognition.lang = 'de-DE'` and change it to `'en-US'`.

## 11. Troubleshooting
- **No Sound?** Check your device volume and if the browser allows audio playback.
- **No Response?** Check if the backend is running and the `VITE_API_URL` in the `.env` file is correct.
- **ADB not working?** Run `setup_adb.bat` again and ensure the tablet screen is on.

## 12. Credits

This project was designed, conceptualized, and developed by:

**Stephan Eck (Protheanreact)**
*Lead Developer & UI/UX Designer*

Thank you for using Haruko AI!
