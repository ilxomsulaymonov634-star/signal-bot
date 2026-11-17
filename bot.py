import asyncio
import random

from database import (
    add_user, get_users_count, get_all_users,
    give_vip, check_vip, update_pocket_id, get_invited_count
)

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.types.web_app_info import WebAppInfo
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# TOKENINGIZNI SHU YERGA YOZING
TOKEN = "9016084815:AAG4zrRit9MHn6KFM0CX5Q4_7HcpKw7HIWw"
ADMIN_ID = 7850429577

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Registration(StatesGroup):
    waiting_for_id = State()

# 📱 SIZNING YANGI MINI ILOVANGIZ VA REFERAL TUGMASI:
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Mini Ilovani ochish", web_app=WebAppInfo(url="https://signal-bot-pro.tiiny.site"))],
        [KeyboardButton(text="📈 Signal"), KeyboardButton(text="📊 Statistika")],
        [KeyboardButton(text="👑 VIP"), KeyboardButton(text="👥 Referal")],
        [KeyboardButton(text="🔧 Admin")]
    ],
    resize_keyboard=True
)

@dp.message(CommandStart())
async def start_command(message: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Referal ID ni tekshiramiz (masalan: /start ref_7850429577)
    args = command.args
    referred_by = None
    if args and args.startswith("ref_"):
        try:
            referred_by = int(args.replace("ref_", ""))
        except ValueError:
            pass

    # Bazaga qo'shamiz (agar referal orqali kirgan bo'lsa, uni ham saqlaymiz)
    add_user(user_id, username, referred_by)
    
    await message.answer(
        "🚀 <b>Pocket Option Pro Botga xush kelibsiz!</b>\n\n"
        "Quyidagi tugmalar yordamida signal olishingiz va do'stlaringizni taklif qilib VIP olishingiz mumkin.",
        reply_markup=menu,
        parse_mode="HTML"
    )

@dp.message(F.text == "👥 Referal")
async def referral_menu(message: Message):
    user_id = message.from_user.id
    invited = get_invited_count(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    await message.answer(
        "👥 <b>Referal Tizimi (Do'stlaringizni taklif qiling)</b>\n\n"
        f"🔗 Sizning shaxsiy havolangiz:\n<code>{ref_link}</code>\n\n"
        f"👤 Siz taklif qilgan do'stlar soni: <b>{invited} ta</b>\n\n"
        "<i>💡 Do'stlaringizni taklif qiling va ularni VIP qilish uchun imkoniyat yarating!</i>",
        parse_mode="HTML"
    )

@dp.message(F.text == "📊 Statistika")
async def statistika(message: Message):
    users = get_users_count()
    await message.answer(f"📊 Statistika\n\n👥 Jami foydalanuvchilar: {users}")

@dp.message(F.text == "🔧 Admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz!")
        return
    users = get_users_count()
    await message.answer(
        f"🔧 ADMIN PANEL\n\n👤 Admin ID: {ADMIN_ID}\n👥 Foydalanuvchilar: {users}\n\n"
        f"📢 Reklama:\n/reklama Matn\n\n👑 VIP berish:\n/vip user_id"
    )

@dp.message(F.text.startswith("/reklama"))
async def send_ads(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = message.text.replace("/reklama", "").strip()
    users = get_all_users()
    count = 0
    for user in users:
        try:
            await bot.send_message(user[0], f"📢 XABARNOMA\n\n{text}")
            count += 1
        except:
            pass
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")

@dp.message(F.text == "📈 Signal")
async def send_signal(message: Message):
    vip = check_vip(message.from_user.id)
    msg = await message.answer("🔄 Bozor holati analiz qilinmoqda (AI)...")
    await asyncio.sleep(1.5)
    await msg.edit_text("📊 Kotirovkalar va indikatorlar tekshirilmoqda...")
    await asyncio.sleep(1.5)

    if vip == 0:
        aktivlar_demo = ["EUR/USD", "GBP/USD", "USD/JPY"]
        signal = random.choice(["BUY 🟢", "SELL 🔴"])
        await msg.edit_text(
            f"⚠️ <b>DEMO SIGNAL</b> ⚠️\n\n📈 <b>Aktiv:</b> {random.choice(aktivlar_demo)}\n⏱ <b>Vaqt:</b> 1 minut\n🎯 <b>Yo'nalish:</b> {signal}\n\n"
            f"<i>🔒 Haqiqiy OTC bozorlar va 95% aniqlik faqat REAL (VIP) hisoblar uchun!\nVIP olish uchun '👑 VIP' tugmasini bosing.</i>",
            parse_mode="HTML"
        )
    else:
        aktivlar_real = ["EUR/USD (OTC)", "GBP/USD (OTC)", "AUD/CAD (OTC)", "USD/JPY (OTC)", "NZD/USD", "EUR/GBP (OTC)"]
        vaqtlar = ["1 minut", "2 minut", "3 minut", "5 minut"]
        signal = random.choice(["BUY 🟢", "SELL 🔴"])
        await msg.edit_text(
            f"⚡️ <b>PRO SIGNAL (REAL)</b> ⚡️\n\n📈 <b>Aktiv:</b> {random.choice(aktivlar_real)}\n⏱ <b>Vaqt:</b> {random.choice(vaqtlar)}\n🎯 <b>Yo'nalish:</b> {signal}\n\n<i>✅ Muvaffaqiyatli savdo tilaymiz!</i>",
            parse_mode="HTML"
        )

@dp.message(F.text == "👑 VIP")
async def vip_menu(message: Message, state: FSMContext):
    vip = check_vip(message.from_user.id)
    if vip == 1:
        await message.answer("✅ Siz allaqachon VIP (Real) foydalanuvchisiz!")
    else:
        await message.answer(
            "👑 <b>VIP Hisobga o'tish!</b>\n\n"
            "1. Mening referal ssilkam orqali Pocket Optiondan ro'yxatdan o'ting.\n"
            "2. Profilingizdagi ID raqamni nusxalang.\n"
            "3. <b>O'sha ID raqamni hozir botga yuboring (masalan: 87654321):</b>",
            parse_mode="HTML"
        )
        await state.set_state(Registration.waiting_for_id)

@dp.message(Registration.waiting_for_id)
async def process_pocket_id(message: Message, state: FSMContext):
    pocket_id = message.text
    user_id = message.from_user.id
    username = message.from_user.username or "Username_yoq"
    
    update_pocket_id(user_id, pocket_id)
    await message.answer(f"✅ ID qabul qilindi: {pocket_id}\n\n⏳ Admin tekshirmoqda. Iltimos kuting...")
    await state.clear()

    inline_btn = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash (VIP)", callback_data=f"vip_give_{user_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"vip_reject_{user_id}")
        ]
    ])
    
    await bot.send_message(
        ADMIN_ID,
        f"👤 <b>Yangi VIP so'rov!</b>\n\nID raqam: <code>{pocket_id}</code>\nTelegram ID: {user_id} (@{username})\n\nUshbu ID sizning Pocket Option referallaringiz ichida bormi?",
        reply_markup=inline_btn,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("vip_"))
async def admin_vip_decision(call: CallbackQuery):
    action = call.data.split("_")[1]
    user_id = int(call.data.split("_")[2])

    if action == "give":
        give_vip(user_id)
        await call.message.edit_text(f"{call.message.text}\n\n✅ <b>Tasdiqlandi va VIP berildi!</b>", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "🎉 <b>TABRIKLAYMIZ!</b>\n\nPocket Option ID raqamingiz tasdiqlandi. Sizga VIP (Real) maqomi berildi!\nEndi xizmatlardan to'liq foydalanishingiz mumkin.", parse_mode="HTML")
        except:
            pass
    elif action == "reject":
        await call.message.edit_text(f"{call.message.text}\n\n❌ <b>Rad etildi!</b>", parse_mode="HTML")
        try:
            await bot.send_message(user_id, "❌ <b>ID Tasdiqlanmadi!</b>\n\nKiritilgan ID raqam referallar ro'yxatidan topilmadi. Iltimos, tekshirib qaytadan urinib ko'ring.", parse_mode="HTML")
        except:
            pass
    await call.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
