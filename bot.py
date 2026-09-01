from telebot import types

# 1. Foydalanuvchi "VIP Obuna" tugmasini bosganda karta va ko'rsatma berish
@bot.message_handler(func=lambda m: m.text == "💳 VIP Obuna (30 kun)")
def request_vip(message):
    user_id = message.from_user.id
    
    bot.send_message(
        user_id,
        "💳 **VIP Obuna to'lovi (30 kun — 30,000 so'm):**\n\n"
        "1. Karta raqami: `8600 1234 5678 9012` (Xusan B.)\n"
        "2. Miqdor: **30,000 so'm**\n\n"
        "📲 Pulni o'tkazgandan so'ng, to'lov cheki (skrinshot) rasmini shu botga yuboring. "
        "Admin tekshirib, obunangizni darhol faollashtiradi.",
        parse_mode="Markdown"
    )

# 2. Foydalanuvchi chek rasmini yuborganda u adminga borishi
@bot.message_handler(content_types=['photo'])
def handle_receipt_photo(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    # DIQQAT: 123456789 o'rniga O'ZINGIZNING Telegram ID raqamingizni yozing!
    ADMIN_ID = 123456789  
    
    # Admin uchun tasdiqlash tugmalari
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_{user_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{user_id}")
    )
    
    # Rasmni adminga yo'naltirish
    bot.forward_message(ADMIN_ID, user_id, message.message_id)
    bot.send_message(
        ADMIN_ID,
        f"👤 Foydalanuvchi: @{username} (ID: `{user_id}`)\n"
        f"Ushbu to'lov chekini tasdiqlaysizmi?",
        parse_mode="Markdown",
        reply_markup=kb
    )
    
    bot.reply_to(message, "⏳ Chekingiz adminga yuborildi. Tez orada tekshirilib, obunangiz faollashtiriladi!")

# 3. Admin tugmani bosganda ishlaydigan qism
@bot.callback_query_handler(func=lambda call: call.data.startswith('approve_') or call.data.startswith('reject_'))
def admin_decision(call):
    data = call.data.split('_')
    action = data[0]
    user_id = int(data[1])
    
    if action == 'approve':
        # BAZANGIZDA foydalanuvchiga VIP obuna yozish funksiyasini shu yerga yozasiz
        # grant_vip_access(user_id)
        
        bot.send_message(user_id, "🎉 Tabriklaymiz! To'lovingiz tasdiqlandi va VIP obuna 30 kunga faollashtirildi!")
        bot.edit_message_text("✅ To'lov tasdiqlandi va foydalanuvchiga obuna berildi.", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(user_id, "❌ Afsuski, to'lov cheki tasdiqlanmadi. Xatolik bo'lsa @admin bilan bog'laning.")
        bot.edit_message_text("❌ To'lov rad etildi.", call.message.chat.id, call.message.message_id)
