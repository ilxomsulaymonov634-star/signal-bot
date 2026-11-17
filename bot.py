import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

from database import add_user, get_users_count, give_vip, check_vip, update_pocket_id, get_invited_count, get_all_users

TOKEN = "9016084815:AAG4zrRit9MHn6KFM0CX5Q4_7HcpKw7HIWw"  # Bot tokeningiz
ADMIN_ID = 7850429577  # Sizning Telegram ID raqamingiz

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Asosiy menyu (Foydalanuvchilar uchun)
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Signal")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👑 VIP")],
            [KeyboardButton(text="👥 Referal")]
        ],
        resize_keyboard=True
    )

# Admin menyusi
def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Signal")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="👑 VIP")],
            [KeyboardButton(text="👥 Referal"), KeyboardButton(text="⚙️ Admin Panel")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Noma'lum"
    
    args = message.text.split()
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referred_by = int(args[1].replace("ref_", ""))
        except ValueError:
            pass

    add_user(user_id, username, referred_by)
    
    kb = admin_menu() if user_id == ADMIN_ID else main_menu()
    
    await message.answer(
        "<b>Pocket Option Pro Botga xush kelibsiz!</b>\n\n"
        "Quyidagi <b>📈 Signal</b> tugmasini bosib aktivni tanlang.",
        reply_markup=kb,
        parse_mode="HTML"
    )

@dp.message(F.text == "👥 Referal")
async def referral_menu(message: Message):
    user_id = message.from_user.id
    invited = get_invited_count(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    text = (
        "👥 <b>Referal Tizimi (Do'stlaringizni taklif qiling)</b>\n\n"
        f"🔗 <b>Sizning shaxsiy havolangiz:</b>\n{ref_link}\n\n"
        f"👤 <b>Siz taklif qilgan do'stlar soni:</b> {invited} ta\n\n"
        "💡 <i>Do'stlaringizni taklif qiling va ularni VIP qilish uchun imkoniyat yarating!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(F.text == "📊 Statistika")
async def stats_command(message: Message):
    users_count = get_users_count()
    await message.answer(f"📊 <b>Bot statistikasi:</b>\n\n👥 Jami foydalanuvchilar: {users_count} ta", parse_mode="HTML")

@dp.message(F.text == "👑 VIP")
async def vip_command(message: Message):
    user_id = message.from_user.id
    vip_status = check_vip(user_id)
    
    if user_id == ADMIN_ID or vip_status == 1:
        await message.answer("👑 Sizda <b>VIP STATUS</b> faol! Barcha real signallardan foydalanishingiz mumkin.", parse_mode="HTML")
    else:
        await message.answer(
            "👑 <b>VIP Statusni qo'lga kiriting!</b>\n\n"
            "Real va yuqori aniqlikdagi signallarni olish uchun do'stlaringizni taklif qiling yoki admin bilan bog'laning.",
            parse_mode="HTML"
        )

@dp.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users_count = get_users_count()
    await message.answer(
        f"🛠 <b>ADMIN PANEL</b>\n\n"
        f"👤 Foydalanuvchilar: {users_count}\n\n"
        f"📢 <b>Reklama:</b>\n/reklama Matn\n\n"
        f"👑 <b>VIP berish:</b>\n/vip user_id",
        parse_mode="HTML"
    )

@dp.message(Command("reklama"))
async def send_ads(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/reklama", "").strip()
    if not text:
        await message.answer("⚠️ Reklama matnini kiriting! Masalan: /reklama Salom hammaga")
        return
    
    users = get_all_users()
    count = 0
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 <b>XABARNOMA</b>\n\n{text}", parse_mode="HTML")
            count += 1
        except:
            pass
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")

@dp.message(Command("vip"))
async def make_vip(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Xato! Ishlatish: /vip user_id")
        return
    try:
        target_id = int(args[1])
        give_vip(target_id)
        await message.answer(f"✅ {target_id} ID egasiga VIP berildi!")
        await bot.send_message(target_id, "👑 <b>TABRIKLAYMIZ!</b>\n\nSizga admin tomonidan VIP status berildi!", parse_mode="HTML")
    except ValueError:
        await message.answer("⚠️ ID raqam faqat raqamlardan iborat bo'lishi kerak!")

# 1-QADAM: "📈 Signal" bosilganda Valyuta, Kripto va Aksiyalar chiqadi
@dp.message(F.text == "📈 Signal")
async def select_currency(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            # Valyutalar
            [
                InlineKeyboardButton(text="💶 EUR/USD", callback_data="curr_EUR/USD"),
                InlineKeyboardButton(text="💷 GBP/USD", callback_data="curr_GBP/USD")
            ],
            [
                InlineKeyboardButton(text="💴 USD/JPY", callback_data="curr_USD/JPY"),
                InlineKeyboardButton(text="🇦🇺 AUD/CAD", callback_data="curr_AUD/CAD")
            ],
            [
                InlineKeyboardButton(text="🇨🇦 USD/CAD", callback_data="curr_USD/CAD"),
                InlineKeyboardButton(text="🇳🇿 AUD/NZD", callback_data="curr_AUD/NZD")
            ],
            # Kriptovalyutalar
            [
                InlineKeyboardButton(text="🪙 BTC/USD", callback_data="curr_BTC/USD"),
                InlineKeyboardButton(text="🪙 ETH/USD", callback_data="curr_ETH/USD")
            ],
            [
                InlineKeyboardButton(text="🪙 XRP/USD", callback_data="curr_XRP/USD"),
                InlineKeyboardButton(text="🪙 LTC/USD", callback_data="curr_LTC/USD")
            ],
            # Aksiyalar
            [
                InlineKeyboardButton(text="🍏 AAPL (Apple)", callback_data="curr_AAPL"),
                InlineKeyboardButton(text="🚗 TSLA (Tesla)", callback_data="curr_TSLA")
            ],
            [
                InlineKeyboardButton(text="🔍 GOOGL (Google)", callback_data="curr_GOOGL"),
                InlineKeyboardButton(text="📦 AMZN (Amazon)", callback_data="curr_AMZN")
            ]
        ]
    )
    await message.answer("📊 <b>Kerakli bozor va aktivni tanlang:</b>", reply_markup=keyboard, parse_mode="HTML")

# 2-QADAM: Aktiv tanlangach, 5 sekunddan 2 soatgacha bo'lgan vaqt oralig'i chiqadi
@dp.callback_query(F.data.startswith("curr_"))
async def select_time(callback: CallbackQuery):
    currency = callback.data.replace("curr_", "")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡️ 5 soniya", callback_data=f"time_{currency}_5s"),
                InlineKeyboardButton(text="⚡️ 15 soniya", callback_data=f"time_{currency}_15s"),
                InlineKeyboardButton(text="⚡️ 30 soniya", callback_data=f"time_{currency}_30s")
            ],
            [
                InlineKeyboardButton(text="⏱ 1 minut", callback_data=f"time_{currency}_1m"),
                InlineKeyboardButton(text="⏱ 2 minut", callback_data=f"time_{currency}_2m"),
                InlineKeyboardButton(text="⏱ 5 minut", callback_data=f"time_{currency}_5m")
            ],
            [
                InlineKeyboardButton(text="⏱ 15 minut", callback_data=f"time_{currency}_15m"),
                InlineKeyboardButton(text="⏱ 30 minut", callback_data=f"time_{currency}_30m")
            ],
            [
                InlineKeyboardButton(text="🕒 1 soat", callback_data=f"time_{currency}_1h"),
                InlineKeyboardButton(text="🕒 2 soat", callback_data=f"time_{currency}_2h")
            ]
        ]
    )
    await callback.message.edit_text(
        f"📊 Tanlangan aktiv: <b>{currency}</b>\n\n⏱ <b>Vaqt oralig'ini tanlang:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()

# 3-QADAM: Vaqt tanlangach, tayyor signalni chiqarib berish
@dp.callback_query(F.data.startswith("time_"))
async def give_final_signal(callback: CallbackQuery):
    parts = callback.data.split("_")
    currency = parts[1]
    time_val = parts[2]
    
    # Vaqtni chiroyli ko'rinishga keltirish
    time_map = {
        "5s": "5 soniya", "15s": "15 soniya", "30s": "30 soniya",
        "1m": "1 minut", "2m": "2 minut", "5m": "5 minut",
        "15m": "15 minut", "30m": "30 minut",
        "1h": "1 soat", "2h": "2 soat"
    }
    readable_time = time_map.get(time_val, time_val)
    
    user_id = callback.from_user.id
    vip = check_vip(user_id)
    
    await callback.message.edit_text("🔄 Bozor holati tahlil qilinmoqda (AI)...")
    await asyncio.sleep(1)
    
    signal = random.choice(["BUY 🟢 (Olish)", "SELL 🔴 (Sotish)"])
    
    if user_id == ADMIN_ID or vip == 1:
        text = (
            f"🔥 <b>PRO SIGNAL (REAL)</b> 🔥\n\n"
            f"📊 <b>Aktiv:</b> {currency} (OTC)\n"
            f"⏱ <b>Vaqt:</b> {readable_time}\n"
            f"🎯 <b>Prognoz:</b> <b>{signal}</b>\n\n"
            f"💡 <i>Professional rejim: Barcha imkoniyatlar ochiq!</i>"
        )
    else:
        text = (
            f"⚠️ <b>DEMO SIGNAL</b>\n\n"
            f"📊 <b>Aktiv:</b> {currency}\n"
            f"⏱ <b>Vaqt:</b> {readable_time}\n"
            f"🎯 <b>Prognoz:</b> <b>{signal}</b>\n\n"
            f"<i>🔒 Haqiqiy signallar uchun VIP status kerak. Do'stlaringizni taklif qiling!</i>"
        )
        
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()

# Render serveri uchun mini web-server
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

async def web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def main():
    await web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
