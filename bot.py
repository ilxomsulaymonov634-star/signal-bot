import os
import time
import asyncio
import threading
import logging
import requests
from flask import Flask
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "9116062179:AAEkGbBgnPtjq54Z39YeJYGykbme1-y_b3I")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "7850429577"))
KEEP_ALIVE_URL = os.environ.get("KEEP_ALIVE_URL", "")

CONTACT_PHONE = "+998900170582"
INSTAGRAM_HANDLE = "@poydevor2413"

app = Flask(__name__)

@app.route("/")
def home():
    return "Instagram AI Agent Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive_ping():
    while True:
        time.sleep(180)
        if KEEP_ALIVE_URL:
            try:
                requests.get(KEEP_ALIVE_URL.strip(), timeout=10)
            except Exception as e:
                logging.warning(f"Keep-alive ping xatosi: {e}")

SYSTEM_INSTRUCTION = f"""
Siz Instagram sahifasi ({INSTAGRAM_HANDLE}) uchun AI kontent va SMM yordamchi agentisiz.
Vazifalaringiz:
1. Yangi AI vositalari va videolar haqida qiziqarli Instagram postlar va Reels ssenariylari tayyorlash.
2. Izohlarga (kommentariyalarga) xushmuomala va foydali javoblar yozish.
3. Zarur hollarda yoki murojaat/aloqa so'ralganda telefon raqami ({CONTACT_PHONE}) va Instagram sahifani ({INSTAGRAM_HANDLE}) eslatib o'tish.
Javoblarni tabiiy, aniq va foydalanuvchiga qulay o'zbek tilida bering.
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"Assalomu alaykum! Men {INSTAGRAM_HANDLE} uchun AI yordamchi botman.\n\n"
        "Menga quyidagilar bo‘yicha murojaat qilishingiz mumkin:\n"
        "• Yangi AI vositalari va videolar haqida post matnlari\n"
        "• Reels va qisqa videolar uchun ssenariylar\n"
        "• Izohlarga tayyor javoblar\n\n"
        f"Instagram: {INSTAGRAM_HANDLE}\n"
        f"Aloqa: {CONTACT_PHONE}"
    )
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        await update.message.reply_text("Xato: GEMINI_API_KEY topilmadi.")
        return

    try:
        ai_client = genai.Client(api_key=api_key)
        response = ai_client.models.generate_content(
            model="gemini-3.8-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )
        reply_text = response.text or "Javob shakllantirishda xatolik yuz berdi."
    except Exception as e:
        logging.error(f"Gemini xatosi: {e}")
        reply_text = f"AI xatosi: {str(e)[:300]}"

    await update.message.reply_text(reply_text)

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive_ping, daemon=True).start()

    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    tg_app.run_polling()

if __name__ == "__main__":
    main()
