import telebot
from telebot import types
import requests
import sqlite3
import time
from datetime import datetime, timedelta

# ==========================================
# REKVIZITLAR
# ==========================================
BOT_TOKEN = "8652148568:AAE8WxclplqJqlbd7Pn7KORerraoFjPalTQ"
OCTO_SHOP_ID = 42970
OCTO_SECRET = "41e5b742-2031-477b-bdb7-d562a46b7a11"

bot = telebot.TeleBot(BOT_TOKEN)

# Bot username'ini avtomatik aniqlash
try:
    BOT_USERNAME = bot.get_me().username
except Exception as e:
    BOT_USERNAME = "bot"

# ==========================================
# MA'LUMOTLAR BAZASI (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            vip_until TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            trans_id TEXT PRIMARY KEY,
            user_id INTEGER,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_user_vip(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT vip_until FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        expire_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        if expire_date > datetime.now():
            return expire_date
    return None

def set_user_vip(user_id, days=30):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    new_expire = datetime.now() + timedelta(days=days)
    expire_str = new_expire.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT OR REPLACE INTO users (user_id, vip_until) VALUES (?, ?)", (user_id, expire_str))
    conn.commit()
    conn.close()

# ==========================================
# KASALLIKLAR BAZASI
# ==========================================
DISEASES = {
    "oq doq": {
        "nom": "Ixtioftirioz (Manka / Oq doqlar)",
        "alomat": "Baliq badanida kichik oq nuqtalar paydo bo'ladi, baliq obyektlarga ishqalanadi.",
        "davo": "1. Suv haroratini 28-30°C ga ko'taring.\n2. Akvariumga 'Kostapur' yoki 'Malaxitoviy zelenyy' qo'shing.\n3. Har kuni suvning 25% qismini tindirilgan suvga almashtiring."
    },
    "suzogich": {
        "nom": "Suzog'ich chirishi (Plavnikovaya gnil)",
        "alomat": "Suzog'ichlar qirralari yeyiladi yoki titilib ketadi.",
        "davo": "1. Suvning 30% qismini almashtiring.\n2. 'Baktopur' yoki 'Levomitsetin' ishlatiladi."
    },
    "paxta": {
        "nom": "Saprolejniya (Zamburug' / Gribok)",
        "alomat": "Tana yuzasida paxtaga o'xshash oq loyqa qoplama.",
        "davo": "1. Baliqni alohida idishga oling.\n2. Tuzli vanna qiling (1L suvga 1 osh qoshiq tuz, 10 daqiqa)."
    }
}

# ==========================================
# MENYU VA MULOQOT
# ==========================================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.from_user.id
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🔬 Kasallikni aniqlash", "📅 Kunlik maslahat")
    kb.row("💳 VIP Obuna (30 kun)", "ℹ️ Obuna holati")
    
    bot.send_message(user_id, 
                     f"Salom {message.from_user.first_name}! 🐠\n\n"
                     f"Men akvarium va baliqlar parvarishi bo'yicha shaxsiy AI-botman.\n"
                     f"Kerakli bo'limni tanlang:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "ℹ️ Obuna holati")
def check_sub_status(message):
    user_id = message.from_user.id
    vip_until = get_user_vip(user_id)
    if vip_until:
        bot.reply_to(message, f"✅ Sizda VIP obuna faol!\n📅 Amal qilish muddati: {vip_until.strftime('%d.%m.%Y %H:%M')} gacha.")
    else:
        bot.reply_to(message, "❌ Sizda hozircha VIP obuna mavjud emas.")

# ==========================================
# OCTO API - TO'LOV YARATISH
# ==========================================
@bot.message_handler(func=lambda m: m.text == "💳 VIP Obuna (30 kun)")
def create_octo_payment(message):
    user_id = message.from_user.id
    trans_id = f"sub_{user_id}_{int(time.time())}"
    
    payload = {
        "octo_shop_id": OCTO_SHOP_ID,
        "octo_secret": OCTO_SECRET,
        "merchant_trans_id": trans_id,
        "amount": 30000.00,
        "currency": "UZS",
        "description": "30 kunlik VIP Obuna",
        "return_url": f"https://t.me/{BOT_USERNAME}"
    }
    
    try:
        res = requests.post("https://secure.octo.uz/prepare", json=payload, timeout=10)
        data = res.json()
        
        if data.get("error") == 0 and "octo_pay_url" in data:
            pay_url = data["octo_pay_url"]
            
            conn = sqlite3.connect("bot_database.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO payments (trans_id, user_id, status) VALUES (?, ?, ?)", (trans_id, user_id, "pending"))
            conn.commit()
            conn.close()
            
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💳 Octo orqali to'lash (30,000 so'm)", url=pay_url))
            kb.add(types.InlineKeyboardButton("🔄 To'lovni tekshirish", callback_data=f"check_{trans_id}"))
            
            bot.send_message(user_id, "VIP obuna sotib olish uchun **To'lash** tugmasini bosing va to'lov qilgach **'To'lovni tekshirish'** tugmasini bosing:", reply_markup=kb)
        else:
            bot.send_message(user_id, "❌ Octo tizimiga ulanishda xatolik bo'ldi. Merchant sozlamalarini tekshiring.")
    except Exception as e:
        bot.send_message(user_id, "❌ Server bilan aloqa o'rnatib bo'lmadi.")

# ==========================================
# OCTO API - TO'LOVNI TEKSHIRISH
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_"))
def verify_octo_payment(call):
    trans_id = call.data.replace("check_", "")
    user_id = call.from_user.id
    
    payload = {
        "octo_shop_id": OCTO_SHOP_ID,
        "octo_secret": OCTO_SECRET,
        "merchant_trans_id": trans_id
    }
    
    try:
        res = requests.post("https://secure.octo.uz/check", json=payload, timeout=10)
        data = res.json()
        
        status = data.get("status")
        
        if status in ["succeeded", "paid"]:
            set_user_vip(user_id, days=30)
            bot.answer_callback_query(call.id, "✅ To'lov muvaffaqiyatli o'tdi!", show_alert=True)
            bot.send_message(user_id, "🎉 Tabriklaymiz! Sizning 30 kunlik VIP obunangiz avtomatik faollashtirildi.")
        else:
            bot.answer_callback_query(call.id, "⏳ To'lov hali amalga oshirilmadi.", show_alert=True)
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ Tekshirishda xatolik yuz berdi.", show_alert=True)

# ==========================================
# AI KASALLIK VA SANOAT MULOQOTI
# ==========================================
@bot.message_handler(func=lambda m: m.text == "🔬 Kasallikni aniqlash")
def ask_disease(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("⚪ Oq nuqtalar (Manka)", callback_data="dis_oq doq"))
    kb.add(types.InlineKeyboardButton("✂️ Suzog'ichlar titilishi", callback_data="dis_suzogich"))
    kb.add(types.InlineKeyboardButton("☁️ Paxtaga o'xshash qoplama", callback_data="dis_paxta"))
    bot.send_message(message.chat.id, "Baliqda qanday alomat ko'ryapsiz?", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("dis_"))
def show_dis_info(call):
    dis_key = call.data.replace("dis_", "")
    if dis_key in DISEASES:
        info = DISEASES[dis_key]
        text = f"📋 **Kasallik:** {info['nom']}\n\n🔍 **Alomati:** {info['alomat']}\n\n💊 **Davolash:**\n{info['davo']}"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📅 Kunlik maslahat")
def daily_tip(message):
    bot.send_message(message.chat.id, "🐠 **Kunlik maslahat:** Baliqlarga yemni kam-kamdan bering. Yem 2 daqiqada yeb tugatilishi kerak. Ortiqcha yem suvni buzadi!")

@bot.message_handler(func=lambda m: True)
def text_ai_chat(message):
    txt = message.text.lower()
    if any(w in txt for w in ["salom", "assalom", "privet"]):
        bot.reply_to(message, "Salom! Baliqlaringiz ahvoli yaxshimi? Bugun yem berdingizmi? 🐠")
    elif "suv" in txt:
        bot.reply_to(message, "💧 Akvarium suvining 20-30% qismini har hafta almashtirib turing.")
    elif "yem" in txt:
        bot.reply_to(message, "🍽️ Yemni kuniga 1-2 marta bering, oshiqchasi suvni kirlatadi.")
    else:
        bot.reply_to(message, "🤖 Men akvarium va baliqlar parvarishi bo'yicha yordamchiman. Savollaringizni berishingiz mumkin!")

bot.infinity_polling()
  
