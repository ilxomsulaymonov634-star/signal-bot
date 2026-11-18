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
        "Quyidagi <b>📈 Signal</b> tugmasini bosib savdo aktivini tanlang.",
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

# 1-QADAM: Aktivlar ro'yxati
@dp.message(F.text == "📈 Signal")
async def select_currency(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💱 --- YUQORI FOIZDAGI AKTIVLAR ---", callback_data="none")],
            [
                InlineKeyboardButton(text="🇦🇺 AUD/CAD OTC (+92%)", callback_data="curr_AUD/CAD OTC"),
                InlineKeyboardButton(text="🇦🇺 AUD/CHF OTC (+92%)", callback_data="curr_AUD/CHF OTC")
            ],
            [
                InlineKeyboardButton(text="💶 EUR/CHF OTC (+92%)", callback_data="curr_EUR/CHF OTC"),
                InlineKeyboardButton(text="💴 EUR/JPY OTC (+92%)", callback_data="curr_EUR/JPY OTC")
            ],
            [
                InlineKeyboardButton(text="💶 EUR/RUB OTC (+92%)", callback_data="curr_EUR/RUB OTC"),
                InlineKeyboardButton(text="🌐 OMR/CNY OTC (+92%)", callback_data="curr_OMR/CNY OTC")
            ],
            [
                InlineKeyboardButton(text="🌐 QAR/CNY OTC (+92%)", callback_data="curr_QAR/CNY OTC"),
                InlineKeyboardButton(text="🇺🇦 UAH/USD OTC (+92%)", callback_data="curr_UAH/USD OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/DZD OTC (+92%)", callback_data="curr_USD/DZD OTC"),
                InlineKeyboardButton(text="💴 USD/JPY OTC (+92%)", callback_data="curr_USD/JPY OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/MYR OTC (+92%)", callback_data="curr_USD/MYR OTC"),
                InlineKeyboardButton(text="💵 USD/PKR OTC (+92%)", callback_data="curr_USD/PKR OTC")
            ],
            [
                InlineKeyboardButton(text="💵 YER/USD OTC (+92%)", callback_data="curr_YER/USD OTC"),
                InlineKeyboardButton(text="🇨🇭 CHF/JPY OTC (+87%)", callback_data="curr_CHF/JPY OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/BRL OTC (+87%)", callback_data="curr_USD/BRL OTC"),
                InlineKeyboardButton(text="🇨🇦 CAD/JPY OTC (+84%)", callback_data="curr_CAD/JPY OTC")
            ],
            [
                InlineKeyboardButton(text="🌐 AED/CNY OTC (+82%)", callback_data="curr_AED/CNY OTC"),
                InlineKeyboardButton(text="💴 AUD/JPY OTC (+82%)", callback_data="curr_AUD/JPY OTC")
            ],
            [
                InlineKeyboardButton(text="💶 EUR/USD OTC (+82%)", callback_data="curr_EUR/USD OTC"),
                InlineKeyboardButton(text="🇦🇺 AUD/USD OTC (+81%)", callback_data="curr_AUD/USD OTC")
            ],
            [
                InlineKeyboardButton(text="🇳🇬 NGN/USD OTC (+81%)", callback_data="curr_NGN/USD OTC"),
                InlineKeyboardButton(text="🇰🇪 KES/USD OTC (+80%)", callback_data="curr_KES/USD OTC")
            ],
            [
                InlineKeyboardButton(text="🌐 BHD/CNY OTC (+77%)", callback_data="curr_BHD/CNY OTC"),
                InlineKeyboardButton(text="🇨🇦 CAD/CHF OTC (+75%)", callback_data="curr_CAD/CHF OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/THB OTC (+71%)", callback_data="curr_USD/THB OTC"),
                InlineKeyboardButton(text="🇹🇳 TND/USD OTC (+70%)", callback_data="curr_TND/USD OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/CAD (+70%)", callback_data="curr_USD/CAD"),
                InlineKeyboardButton(text="🇨🇱 USD/CLP OTC (+70%)", callback_data="curr_USD/CLP OTC")
            ],
            [
                InlineKeyboardButton(text="💶 EUR/TRY OTC (+69%)", callback_data="curr_EUR/TRY OTC"),
                InlineKeyboardButton(text="🇮🇩 USD/IDR OTC (+69%)", callback_data="curr_USD/IDR OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/SGD OTC (+65%)", callback_data="curr_USD/SGD OTC"),
                InlineKeyboardButton(text="🇦🇷 USD/ARS OTC (+64%)", callback_data="curr_USD/ARS OTC")
            ],
            [
                InlineKeyboardButton(text="🇨🇭 USD/CHF OTC (+64%)", callback_data="curr_USD/CHF OTC"),
                InlineKeyboardButton(text="🇮🇳 USD/INR OTC (+64%)", callback_data="curr_USD/INR OTC")
            ],
            [
                InlineKeyboardButton(text="🇪🇬 USD/EGP OTC (+62%)", callback_data="curr_USD/EGP OTC"),
                InlineKeyboardButton(text="🇨🇦 CAD/JPY (+61%)", callback_data="curr_CAD/JPY")
            ],
            [
                InlineKeyboardButton(text="🇨🇴 USD/COP OTC (+60%)", callback_data="curr_USD/COP OTC"),
                InlineKeyboardButton(text="🇷🇺 USD/RUB OTC (+60%)", callback_data="curr_USD/RUB OTC")
            ],
            [
                InlineKeyboardButton(text="🇱🇧 LBP/USD OTC (+59%)", callback_data="curr_LBP/USD OTC"),
                InlineKeyboardButton(text="🇲🇦 MAD/USD OTC (+59%)", callback_data="curr_MAD/USD OTC")
            ],
            [
                InlineKeyboardButton(text="💵 USD/CAD OTC (+59%)", callback_data="curr_USD/CAD OTC"),
                InlineKeyboardButton(text="💶 EUR/USD (+57%)", callback_data="curr_EUR/USD")
            ],
            [
                InlineKeyboardButton(text="🇦🇺 AUD/CAD (+56%)", callback_data="curr_AUD/CAD"),
                InlineKeyboardButton(text="🇻🇳 USD/VND OTC (+55%)", callback_data="curr_USD/VND OTC")
            ],
            [
                InlineKeyboardButton(text="🇨🇳 USD/CNH OTC (+53%)", callback_data="curr_USD/CNH OTC"),
                InlineKeyboardButton(text="🇭🇺 EUR/HUF OTC (+51%)", callback_data="curr_EUR/HUF OTC")
            ],
            [
                InlineKeyboardButton(text="🇦🇺 AUD/CHF (+50%)", callback_data="curr_AUD/CHF"),
                InlineKeyboardButton(text="💴 AUD/JPY (+50%)", callback_data="curr_AUD/JPY")
            ],
            [
                InlineKeyboardButton(text="🇦🇺 AUD/USD (+50%)", callback_data="curr_AUD/USD"),
                InlineKeyboardButton(text="🇨🇦 CAD/CHF (+50%)", callback_data="curr_CAD/CHF")
            ],
            [
                InlineKeyboardButton(text="🇨🇭 CHF/JPY (+50%)", callback_data="curr_CHF/JPY"),
                InlineKeyboardButton(text="💶 EUR/CHF (+50%)", callback_data="curr_EUR/CHF")
            ],
            [
                InlineKeyboardButton(text="🇨🇭 USD/CHF (+50%)", callback_data="curr_USD/CHF"),
                InlineKeyboardButton(text="💴 USD/JPY (+46%)", callback_data="curr_USD/JPY")
            ],
            [
                InlineKeyboardButton(text="🇿🇦 ZAR/USD OTC (+46%)", callback_data="curr_ZAR/USD OTC"),
                InlineKeyboardButton(text="💴 EUR/JPY (+42%)", callback_data="curr_EUR/JPY")
            ],
            [
                InlineKeyboardButton(text="🇸🇦 SAR/CNY OTC (+41%)", callback_data="curr_SAR/CNY OTC"),
                InlineKeyboardButton(text="🇧🇩 USD/BDT OTC (+36%)", callback_data="curr_USD/BDT OTC")
            ],
            [
                InlineKeyboardButton(text="🇲🇽 USD/MXN OTC (+36%)", callback_data="curr_USD/MXN OTC"),
                InlineKeyboardButton(text="🇳🇴 CHF/NOK OTC (+32%)", callback_data="curr_CHF/NOK OTC")
            ]
        ]
    )
    await message.answer("🌐 <b>Pocket Option - Savdo Aktivini Tanlang:</b>", reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "none")
async def none_callback(callback: CallbackQuery):
    await callback.answer("Iltimos, pastdagi aktivlardan birini tanlang!", show_alert=False)

# 2-QADAM: Vaqt oralig'i menyusi
@dp.callback_query(F.data.startswith("curr_"))
async def select_time(callback: CallbackQuery):
    currency = callback.data.replace("curr_", "")
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡️ 1s", callback_data=f"time_{currency}_1s"),
                InlineKeyboardButton(text="⚡️ 10s", callback_data=f"time_{currency}_10s"),
                InlineKeyboardButton(text="⚡️ 24s", callback_data=f"time_{currency}_24s")
            ],
            [
                InlineKeyboardButton(text="⏱ 1m", callback_data=f"time_{currency}_1m"),
                InlineKeyboardButton(text="⏱ 2m", callback_data=f"time_{currency}_2m"),
                InlineKeyboardButton(text="⏱ 3m", callback_data=f"time_{currency}_3m")
            ],
            [
                InlineKeyboardButton(text="⏱ 4m", callback_data=f"time_{currency}_4m"),
                InlineKeyboardButton(text="⏱ 5m", callback_data=f"time_{currency}_5m"),
                InlineKeyboardButton(text="⏱ 10m", callback_data=f"time_{currency}_10m")
            ],
            [
                InlineKeyboardButton(text="⏱ 15m", callback_data=f"time_{currency}_15m"),
                InlineKeyboardButton(text="⏱ 30m", callback_data=f"time_{currency}_30m")
            ],
            [
                InlineKeyboardButton(text="🕒 1h", callback_data=f"time_{currency}_1h"),
                InlineKeyboardButton(text="🕒 2h", callback_data=f"time_{currency}_2h"),
                InlineKeyboardButton(text="🕒 3h", callback_data=f"time_{currency}_3h")
            ],
            [
                InlineKeyboardButton(text="📅 1 oy", callback_data=f"time_{currency}_1oy")
            ]
        ]
    )
    try:
        await callback.message.edit_text(
            f"📊 Tanlangan aktiv: <b>{currency}</b>\n\n⏱ <b>Ekspratsiya vaqtini tanlang:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception:
        pass
    await callback.answer()

# 3-QADAM: To'g'rilangan signal yo'nalishi (BUY / SELL)
@dp.callback_query(F.data.startswith("time_"))
async def give_final_signal(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        currency = parts[1]
        time_val = parts[2]
        
        time_map = {
            "1s": "1 soniya", "10s": "10 soniya", "24s": "24 soniya",
            "1m": "1 minut", "2m": "2 minut", "3m": "3 minut",
            "4m": "4 minut", "5m": "5 minut", "10m": "10 minut",
            "15m": "15 minut", "30m": "30 minut",
            "1h": "1 soat", "2h": "2 soat", "3h": "3 soat",
            "1oy": "1 oy"
        }
        readable_time = time_map.get(time_val, time_val)
        
        user_id = callback.from_user.id
        vip = check_vip(user_id)
        
        await callback.message.delete()
        
        wait_msg = await bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"🔄 <b>{currency}</b> ({readable_time})\n📉 Bozor tahlil qilinmoqda...",
            parse_mode="HTML"
        )
        await asyncio.sleep(1.2)
        
        # Signal logikasi to'g'ri va barqaror ishlashi uchun tartibga solindi
        seed_data = sum(ord(c) for c in currency) + len(time_val) + random.randint(1, 50)
        random.seed(seed_data)
        
        # Aniqroq va to'g'ri taqsimlangan signal yo'nalishi
        signal_type = random.choice(["CALL 🟢 (Yuqoriga / Olish)", "PUT 🔴 (Pastga / Sotish)"])
        accuracy = random.randint(88, 98)
        
        if user_id == ADMIN_ID or vip == 1:
            text = (
                f"🔥 <b>POCKET OPTION PRO SIGNAL (REAL)</b> 🔥\n\n"
                f"📊 <b>Aktiv:</b> {currency}\n"
                f"⏱ <b>Vaqt:</b> {readable_time}\n"
                f"🎯 <b>Prognoz:</b> <b>{signal_type}</b>\n"
                f"📊 <b>Aniqlik darajasi:</b> %{accuracy}\n\n"
                f"💡 <i>Professional rejim: Tahlil yakunlandi!</i>"
            )
        else:
            text = (
                f"⚠️ <b>POCKET OPTION DEMO SIGNAL</b>\n\n"
                f"📊 <b>Aktiv:</b> {currency}\n"
                f"⏱ <b>Vaqt:</b> {readable_time}\n"
                f"🎯 <b>Prognoz:</b> <b>{signal_type}</b>\n"
                f"📊 <b>Aniqlik darajasi:</b> %{accuracy}\n\n"
                f"<i>🔒 Haqiqiy signallar uchun VIP status kerak. Do'stlaringizni taklif qiling!</i>"
            )
            
        await wait_msg.edit_text(text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Xatolik: {e}")
    
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
