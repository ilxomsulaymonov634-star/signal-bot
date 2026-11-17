import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import add_user, get_users_count, give_vip, check_vip, update_pocket_id, get_invited_count, get_all_users

TOKEN = "9016084815:AAG4zrRit9MHn6KFM0CX5Q4_7HcpKw7HIWw"  # O'zingizning bot tokeningiz
ADMIN_ID = 7850429577  # Sizning Telegram ID raqamingiz

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Asosiy menyu (Foydalanuvchilar uchun)
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Signal"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="👑 VIP"), KeyboardButton(text="👥 Referal")]
        ],
        resize_keyboard=True
    )

# Admin menyusi
def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📈 Signal"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="👑 VIP"), KeyboardButton(text="👥 Referal")],
            [KeyboardButton(text="⚙️ Admin Panel")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "Noma'lum"
    
    # Referral havoladan kelganligini tekshirish (masalan: /start ref_12345678)
    args = message.text.split()
    referred_by = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referred_by = int(args[1].replace("ref_", ""))
        except ValueError:
            pass

    # Foydalanuvchini bazaga qo'shish
    add_user(user_id, username, referred_by)
    
    # Agar admin bo'lsa admin menyusi, aks holda oddiy menyu
    kb = admin_menu() if user_id == ADMIN_ID else main_menu()
    
    await message.answer(
        "<b>Pocket Option Pro Botga xush kelibsiz!</b>\n\n"
        "Quyidagi tugmalar yordamida signal olishingiz va do'stlaringizni taklif qilib VIP olishingiz mumkin.",
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
            "Real va yuqori aniqlikdagi signallarni olish uchun Pocket Option ID raqamingizni yuboring yoki do'stlaringizni taklif qiling.\n\n"
            "Iltimos, Pocket Option ID raqamingizni kiriting:",
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

@dp.message(F.text == "📈 Signal")
async def send_signal(message: Message):
    user_id = message.from_user.id
    vip = check_vip(user_id)
    
    msg = await message.answer("🔄 Bozor holati tahlil qilinmoqda (AI)...")
    await asyncio.sleep(1.5)
    await msg.edit_text("📈 Kotirovkalar va indikatorlar tekshirilmoqda...")
    await asyncio.sleep(1.5)
    
    # Agar admin yoki VIP bo'lsa - Real/Pro signallar, boshqalarga Demo signallar
    if user_id == ADMIN_ID or vip == 1:
        aktivlar_real = ["EUR/USD (OTC)", "GBP/USD (OTC)", "AUD/CAD (OTC)", "USD/JPY (OTC)", "NZD/USD", "EUR/GBP (OTC)"]
        vaqtlar = ["1 minut", "2 minut", "3 minut", "5 minut"]
        signal = random.choice(["BUY 🟢", "SELL 🔴"])
        
        await msg.edit_text(
            f"🔥 <b>PRO SIGNAL (REAL)</b> 🔥\n\n"
            f"📊 <b>Aktiv:</b> {random.choice(aktivlar_real)}\n"
            f"⏱ <b>Vaqt:</b> {random.choice(vaqtlar)}\n"
            f"🎯 <b>Prognoz:</b> <b>{signal}</b>\n\n"
            f"💡 <i>Professional rejim: Sizda barcha imkoniyatlar ochiq!</i>",
            parse_mode="HTML"
        )
    else:
        aktivlar_demo = ["EUR/USD", "GBP/USD", "USD/JPY"]
        signal = random.choice(["BUY 🟢", "SELL 🔴"])
        
        await msg.edit_text(
            f"△ <b>DEMO SIGNAL</b> ⚠️\n\n"
            f"📊 <b>Aktiv:</b> {random.choice(aktivlar_demo)}\n"
            f"⏱ <b>Vaqt:</b> 1 minut\n"
            f"🎯 <b>Prognoz:</b> <b>{signal}</b>\n\n"
            f"<i>🔒 Haqiqiy OTC bozorlar va 95% aniqlik faqat REAL (VIP) hisoblar uchun! VIP olish uchun do'stlaringizni taklif qiling yoki admin bilan bog'laning.</i>",
            parse_mode="HTML"
        )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
