import os
import asyncio
import threading
import time
import logging
import requests
from flask import Flask
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
RAW_KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL", "https://signal-bot-hesg.onrender.com").strip()
KEEP_ALIVE_URL = RAW_KEEP_ALIVE_URL.strip("[]()<>\"' ").strip()

app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot ishlayapti!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

def keep_alive_loop():
    if not KEEP_ALIVE_URL.startswith("http"):
        return
    while True:
        time.sleep(300)
        try:
            requests.get(KEEP_ALIVE_URL, timeout=15)
        except Exception as e:
            logger.warning(f"Keep-alive ping xatosi: {e}")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Bot ishga tushdi.\n"
        "Xabar yoki mavzu yozing, javob beraman."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = (update.message.text or "").strip()
    if not user_text:
        return

    if not client:
        await update.message.reply_text("GEMINI_API_KEY sozlanmagan.")
        return

    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_text,
        )
        reply_text = (response.text or "").strip() or "Javob qaytarilmadi."
        await update.message.reply_text(reply_text)
    except Exception as e:
        logger.error(f"Gemini xatosi: {e}")
        await update.message.reply_text(f"Xatolik yuz berdi: {e}")

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN topilmadi!")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive_loop, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot polling boshlandi...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
