import os
import asyncio
import threading
import time
import logging
import requests
from flask import Flask
from google import genai
from google.genai import types
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

def ask_gemini_with_retry(prompt: str) -> str:
    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="Javoblarni o'zbek tilida, aniq, lo'nda va ortiqcha cho'zmasdan yoz.",
                    max_output_tokens=600,
                    temperature=0.7,
                ),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as e:
            last_error = e
            logger.warning(f"Urinish {attempt + 1}/3 xatosi: {e}")
            time.sleep(2)
    raise last_error or RuntimeError("Model javob qaytarmadi.")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Bot yangilandi.\n"
        "Savol yoki mavzu yozing, tez va aniq javob beraman."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = (update.message.text or "").strip()
    if not user_text:
        return

    if not client:
        await update.message.reply_text("GEMINI_API_KEY sozlanmagan.")
        return

    waiting_msg = await update.message.reply_text("⏳ Javob tayyorlanmoqda...")

    try:
        reply_text = await asyncio.wait_for(
            asyncio.to_thread(ask_gemini_with_retry, user_text),
            timeout=35.0
        )
        if len(reply_text) > 4000:
            reply_text = reply_text[:4000] + "..."
        await waiting_msg.edit_text(reply_text)
    except asyncio.TimeoutError:
        await waiting_msg.edit_text("⚠️ Server javobi kechikdi. Iltimos, savolni qisqaroq qilib qayta yuboring.")
    except Exception as e:
        logger.error(f"Gemini xatosi: {e}")
        err_str = str(e)
        if "503" in err_str or "UNAVAILABLE" in err_str:
            await waiting_msg.edit_text("⚠️ AI serveri hozir band (503). 10 soniyadan keyin qayta yuboring.")
        else:
            await waiting_msg.edit_text(f"Xatolik yuz berdi: {err_str[:300]}")

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
