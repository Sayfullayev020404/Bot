import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from datetime import datetime
TOKEN = "7091384260:AAF_Spm-l6AC3xE7o0LyLgiOb2RjLyI7-mA"
CHANNEL_ID = "-1002072810007"


bot = telebot.TeleBot(TOKEN)

user_data = {}  # Foydalanuvchilar kiritgan ma'lumotlar
user_votes = {}  # Foydalanuvchilarning ovoz berishini saqlash

def check_membership(user_id):
    """Foydalanuvchi kanalga a'zo ekanligini tekshiradi"""
    url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={CHANNEL_ID}&user_id={user_id}"
    response = requests.get(url).json()
    status = response.get("result", {}).get("status", "")
    return status in ["member", "administrator", "creator"]

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {"date": None, "text": None, "variants": [], "chat_id": user_id, "message_id": None}
    bot.send_message(user_id, "📅 Ovoz berish tugash sanasini kiriting (YYYY-MM-DD formatda):")
    bot.register_next_step_handler(message, get_date)

def get_date(message):
    """Foydalanuvchidan tugash sanasini oladi"""
    user_id = message.chat.id
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d").date()
        if end_date < datetime.today().date():
            bot.send_message(user_id, "⚠️ Tugash sanasi bugundan oldin bo‘lishi mumkin emas! Qayta kiriting:")
            bot.register_next_step_handler(message, get_date)
            return
        user_data[user_id]["date"] = end_date
        bot.send_message(user_id, "📌 Matnni kiriting:")
        bot.register_next_step_handler(message, get_text)
    except ValueError:
        bot.send_message(user_id, "❌ Noto‘g‘ri format! Tugash sanasini YYYY-MM-DD formatda kiriting:")
        bot.register_next_step_handler(message, get_date)

def get_text(message):
    """Matnni qabul qiladi va variantlarni kiritishni so‘raydi"""
    user_id = message.chat.id
    user_data[user_id]["text"] = message.text
    bot.send_message(user_id, "📌 Variantlarni kiriting (Har birini alohida yuboring). Tugatish uchun 'Tugatish' deb yozing.")
    bot.register_next_step_handler(message, get_variants)

def get_variants(message):
    """Variantlarni ketma-ket qabul qiladi"""
    user_id = message.chat.id
    if message.text.lower() == "tugatish":
        send_poll(user_id)
        return
    user_data[user_id]["variants"].append({"text": message.text, "votes": 0})
    bot.send_message(user_id, "🔹 Yana bir variant kiriting yoki 'Tugatish' deb yozing.")
    bot.register_next_step_handler(message, get_variants)

def send_poll(user_id):
    """Ovoz berish xabarini kanalga yuboradi"""
    poll_data = user_data.get(user_id)
    if not poll_data or not poll_data["variants"]:
        bot.send_message(user_id, "⚠️ Hech qanday variant kiritilmadi.")
        return
    
    text = f"📊 {poll_data['text']}\n🗓 Tugash sanasi: {poll_data['date']}\n\nOvoz berish uchun variantni bosing:"
    markup = InlineKeyboardMarkup()
    for i, variant in enumerate(poll_data["variants"]):
        markup.add(InlineKeyboardButton(text=f"{variant['text']} (0)", callback_data=f"vote_{user_id}_{i}"))

    # Xabarni kanalda yuborish
    sent_message = bot.send_message(CHANNEL_ID, text, reply_markup=markup)
    poll_data["message_id"] = sent_message.message_id
    bot.send_message(user_id, "✅ Ovoz berish xabari kanalga joylandi!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("vote_"))
def vote(call):
    """Ovoz berish tugmasi bosilganda ishlaydi"""
    user_id = call.from_user.id
    _, owner_id, index = call.data.split("_")
    owner_id = int(owner_id)
    index = int(index)

    if owner_id not in user_data:
        bot.answer_callback_query(call.id, "❌ Ovoz berish tugadi yoki mavjud emas.")
        return

    poll_data = user_data[owner_id]
    end_date = poll_data["date"]

    # Ovoz berish muddati tugaganini tekshirish
    if datetime.today().date() > end_date:
        bot.answer_callback_query(call.id, "⛔ Ovoz berish muddati tugagan!", show_alert=True)
        return

# Kanal a'zoligini tekshirish
    if not check_membership(user_id):
        bot.answer_callback_query(call.id, "⛔ Ovoz berish uchun kanalga a'zo bo‘lishingiz kerak!", show_alert=True)
        return

    # Har bir foydalanuvchi faqat 1 marta ovoz berishi mumkin
    if user_id in user_votes.get(owner_id, set()):
        bot.answer_callback_query(call.id, "⚠️ Siz allaqachon ovoz bergansiz!")
        return

    # Ovoz qo‘shish va xabarni yangilash
    user_votes.setdefault(owner_id, set()).add(user_id)
    poll_data["variants"][index]["votes"] += 1
    update_poll_message(owner_id)

    bot.answer_callback_query(call.id, "✅ Ovoz qabul qilindi!")

def update_poll_message(owner_id):
    """Ovozlar yangilangan holatda xabarni kanalga qayta chiqaradi"""
    poll_data = user_data[owner_id]
    text = f"📊 {poll_data['text']}\n🗓 Tugash sanasi: {poll_data['date']}\n\nOvoz berish uchun variantni bosing:"
    
    markup = InlineKeyboardMarkup()
    for i, variant in enumerate(poll_data["variants"]):
        markup.add(InlineKeyboardButton(text=f"{variant['text']} ({variant['votes']})", callback_data=f"vote_{owner_id}_{i}"))
    
    bot.edit_message_text(text, CHANNEL_ID, poll_data["message_id"], reply_markup=markup)

bot.infinity_polling()
# Kanal a'zoligini tekshirish
    if not check_membership(user_id):
        bot.answer_callback_query(call.id, "⛔ Ovoz berish uchun kanalga a'zo bo‘lishingiz kerak!", show_alert=True)
        return

    # Har bir foydalanuvchi faqat 1 marta ovoz berishi mumkin
    if user_id in user_votes.get(owner_id, set()):
        bot.answer_callback_query(call.id, "⚠️ Siz allaqachon ovoz bergansiz!")
        return

    # Ovoz qo‘shish va xabarni yangilash
    user_votes.setdefault(owner_id, set()).add(user_id)
    poll_data["variants"][index]["votes"] += 1
    update_poll_message(owner_id)

    bot.answer_callback_query(call.id, "✅ Ovoz qabul qilindi!")

def update_poll_message(owner_id):
    """Ovozlar yangilangan holatda xabarni kanalga qayta chiqaradi"""
    poll_data = user_data[owner_id]
    text = f"📊 {poll_data['text']}\n🗓 Tugash sanasi: {poll_data['date']}\n\nOvoz berish uchun variantni bosing:"
    
    markup = InlineKeyboardMarkup()
    for i, variant in enumerate(poll_data["variants"]):
        markup.add(InlineKeyboardButton(text=f"{variant['text']} ({variant['votes']})", callback_data=f"vote_{owner_id}_{i}"))
    
    bot.edit_message_text(text, CHANNEL_ID, poll_data["message_id"], reply_markup=markup)

bot.infinity_polling()
