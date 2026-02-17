# Frequently Asked Questions (FAQ)

### 1. Why do I get a security warning in the browser?
Because the system uses a self-signed SSL certificate (to allow microphone access over the network), the browser does not automatically trust it.
**Solution**: Click "Advanced" and then "Proceed to ... (unsafe)". This is safe within your private home network.

### 2. My microphone doesn't work on mobile.
- Ensure you are using `https://` (not `http://`). Browsers block microphone access on insecure sites.
- Check if you have granted permission to the browser.
- Select the correct microphone in the dropdown menu (sometimes "Default" is assigned incorrectly).

### 3. The bot is not responding.
- Is the **Backend** running? Check the terminal window for errors.
- **Internet Connection?** The primary AI (Gemini) needs internet. If offline, ensure **Ollama** is running for fallback.
- Is the **IP Address** correct? Check the `frontend/.env` file.

### 4. Smart Home devices are not responding.
- Are the `TUYA_ACCESS_ID` and Secret in `main.py` correct?
- Are the devices online in the Tuya Cloud?
- Restart the backend to refresh the device list.

### 5. How do I add new avatars?
- Save `.vrm` files in the `frontend/public/models/` folder.
- Adjust the logic in `backend/main.py` (`/avatar-check`) to define when which avatar should be loaded.

### 6. ADB / Tablet Control is not working.
- Did you run `setup_adb.bat` on the PC?
- Is the tablet screen ON and unlocked?
- Is "Wireless Debugging" enabled on the tablet?
- Try running `setup_adb.bat` again to repair the connection.

### 7. What is Auto-Memory?
Haruko listens to the conversation and automatically saves important facts (e.g., your name, hobbies). You no longer need to explicitly say "Remember...". The system decides for itself what is relevant.

### 8. How does Self-Learning work?
When you ask Haruko to teach her something (e.g., "Teach me..."), she researches the topic via Gemini, creates an internal guide, and saves it to `knowledge/`. From then on, she can answer questions about it without searching again.

### 9. How can I use Haruko via WhatsApp?
Haruko can chat with you via a local WhatsApp Web bridge:
- Make sure the server is running and `start_haruko_windows.bat` has been started.
- A window "Haruko WhatsApp" opens with a QR code.
- Scan the QR code in WhatsApp under **Linked Devices**.
- Commands:
  - The master number always has full access.
  - Other people can send commands with a password prefix, e.g. `PASSWORD: turn on the lights`.

### 10. How can I change the language?
You can change the language at any time by either:
- Running the setup script (`setup_windows.ps1`) again and selecting the language.
- Or manually editing the `backend/.env` file and changing the line `LANGUAGE=EN` (for English) or `LANGUAGE=DE` (for German). Restart the backend afterwards.

### Credits
Project Lead & Design: **Stephan Eck (Protheanreact)**
