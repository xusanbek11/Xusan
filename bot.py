import os
import telebot
from telebot import types

# Bot tokenini olish (Render Environment Variables orqali yoki to'g'ridan-to'g'ri)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

# Karta va admin ma'lumotlari
CARD_NUMBER = "5614 6810 0569 9115"
CARD_HOLDER = "Xalilov X"
ADMIN_USERNAME = "@Xalkinbey"
PRICE = "19,900"

# VIP foydalanuvchilar ID ro'yxati (Baza ishlatayotgan bo'lsangiz, bazadan tekshiriladi)
vip_users = set()

# Asosiy menyu tugmalari
def get_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔬 Kasallikni aniqlash", "📅 Kunlik maslahat")
    kb.row("💳 VIP Obuna (30 kun)", "ℹ️ Obuna holati")
    return kb

# To'lov yo'riqnomasi matni (O'zbek va Rus tillarida)
def get_payment_text():
    return (
        f"🇺🇿 **VIP (Premium) Obuna to'lovi (30 kun — {PRICE} so'm):**\n\n"
        f"1. Karta raqami: `{CARD_NUMBER}` ({CARD_HOLDER})\n"
        f"2. Miqdor: **{PRICE} so'm**\n\n"
        f"📲 Pulni o'tkazgandan so'ng, to'lov cheki (skrinshot) rasmini {ADMIN_USERNAME} ga yuboring. "
        f"Admin tekshirib, obunangizni qo'lda faollashtiradi.\n\n"
        "-----------------------------------\n\n"
        f"🇷🇺 **Оплата VIP (Premium) подписки (30 дней — {PRICE} сум):**\n\n"
        f"1. Номер карты: `{CARD_NUMBER}` ({CARD_HOLDER})\n"
        f"2. Сумма: **{PRICE} сум**\n\n"
        f"📲 После перевода отправьте чек об оплате (скриншот) администратору {ADMIN_USERNAME}. "
        f"Администратор проверит и активирует вашу подписку вручную."
    )

# /start buyrug'i
@bot.message_handler(commands=['start'])
def start_handler(message):
    welcome_text = (
        "Assalomu alaykum! **BaliqchiAI** botiga xush kelibsiz.\n\n"
        "Akvarium baliqlaringiz parvarishi va maslahatlar olish uchun quyidagi tugmalardan foydalaning."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# 1. Kasallikni aniqlash tugmasi (Faqat VIP uchun)
@bot.message_handler(func=lambda m: m.text in ["🔬 Kasallikni aniqlash", "Kasallikni aniqlash"])
def check_disease(message):
    user_id = message.from_user.id
    
    # Agar foydalanuvchi VIP bo'lmasa to'lov yo'riqnomasi chiqadi:
    if user_id not in vip_users:
        warning_msg = (
            "⚠️ **Kasallikni aniqlash funksiyasi faqat Premium (VIP) foydalanuvchilar uchun!**\n\n"
            f"Baliqlar kasalliklarini aniqlash imkoniyatini ochish uchun Premium tarifi sotib olishingiz kerak.\n\n"
        ) + get_payment_text()
        
        bot.send_message(user_id, warning_msg, parse_mode="Markdown")
        return

    # VIP foydalanuvchilar uchun:
    bot.send_message(
        user_id, 
        "🔬 **Kasallikni aniqlash bo'limi:**\n\n"
        "Iltimos, kasallangan baliqning alomatlarini batafsil yozib yuboring yoki rasmini tashlang."
    )

# 2. Kunlik maslahat tugmasi
@bot.message_handler(func=lambda m: m.text in ["📅 Kunlik maslahat", "Kunlik maslahat"])
def daily_tip(message):
    tip_text = (
        "🐟 **Kunlik maslahat:** Baliqlarga yemni kam-kamdan bering. "
        "Yem 2 daqiqada yeb tugatilishi kerak. Ortiqcha yem suvni buzadi!"
    )
    bot.send_message(message.chat.id, tip_text, parse_mode="Markdown")

# 3. VIP Obuna tugmasi
@bot.message_handler(func=lambda m: m.text in ["💳 VIP Obuna (30 kun)", "💳 VIP Подписка (30 дней)"])
def request_vip(message):
    bot.send_message(message.chat.id, get_payment_text(), parse_mode="Markdown")

# 4. Obuna holati tugmasi
@bot.message_handler(func=lambda m: m.text in ["ℹ️ Obuna holati", "Obuna holati"])
def check_status(message):
    user_id = message.from_user.id
    if user_id in vip_users:
        msg = "✅ Sizda VIP obuna faol!"
    else:
        msg = "❌ Sizda hozircha VIP obuna mavjud emas."
    bot.send_message(user_id, msg)

# Botni ishga tushirish
if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
