import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncio

# Logging konfigurieren
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class HarukoTelegramBot:
    def __init__(self, token, llm_processor, vision_processor):
        self.token = token
        self.llm_processor = llm_processor  # Async function: func(text, source="telegram") -> str
        self.vision_processor = vision_processor # Async function: func(target) -> image_path
        self.application = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Hallo Meister! Haruko ist bereit. \n"
            "Du kannst mit mir chatten oder Befehle nutzen:\n"
            "/cam [raum] - Zeigt ein Bild der Kamera\n"
            "/status - Systemstatus"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Befehle:\n/cam - Screenshot\n/status - Statusbericht"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_text = update.message.text
        chat_id = update.effective_chat.id
        
        # Sende "Tippt..." Status
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        try:
            # Antwort vom LLM holen
            response = await self.llm_processor(user_text, source="telegram")
            
            # Telegram hat ein Limit von 4096 Zeichen. Falls länger, splitten.
            if len(response) > 4000:
                for x in range(0, len(response), 4000):
                    await update.message.reply_text(response[x:x+4000])
            else:
                await update.message.reply_text(response)
        except Exception as e:
            await update.message.reply_text(f"Fehler: {e}")

    async def cam_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        target = "screen"
        if args:
            target = " ".join(args)
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")
        
        try:
            image_path = await self.vision_processor(target)
            if image_path and os.path.exists(image_path):
                await update.message.reply_photo(photo=open(image_path, 'rb'))
            else:
                await update.message.reply_text("Konnte kein Bild aufnehmen.")
        except Exception as e:
            await update.message.reply_text(f"Kamera-Fehler: {e}")

    def initialize(self):
        if not self.token or self.token == "YOUR_TELEGRAM_TOKEN":
            print("[TELEGRAM] Kein Token konfiguriert. Bot startet nicht.")
            return None

        self.application = ApplicationBuilder().token(self.token).build()
        
        start_handler = CommandHandler('start', self.start)
        help_handler = CommandHandler('help', self.help_command)
        cam_handler = CommandHandler('cam', self.cam_command)
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)

        self.application.add_handler(start_handler)
        self.application.add_handler(help_handler)
        self.application.add_handler(cam_handler)
        self.application.add_handler(msg_handler)
        
        return self.application

    async def start_polling(self):
        if self.application:
            try:
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling()
                print("[TELEGRAM] Bot läuft und hört zu.")
            except Exception as e:
                print(f"[TELEGRAM] Fehler beim Starten: {e}")
    
    async def stop(self):
        if self.application:
            print("[TELEGRAM] Stoppe Bot...")
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            except Exception as e:
                print(f"[TELEGRAM] Fehler beim Stoppen: {e}")