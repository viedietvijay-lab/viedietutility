# profile.py
import telebot
from config import BOT_TOKEN
from database import Database
from buttons import back_button

from bot_instance import bot
db = Database()

@bot.callback_query_handler(func=lambda call: call.data == "menu:profile")
def show_profile(call):
    user_id = call.from_user.id
    user = db.get_user(user_id)
    if user:
        banned, _ = db.is_banned(user_id)
        premium = db.is_premium(user_id)
        text = f"""
👤 <b>Profile</b>

🆔 ID: <code>{user_id}</code>
👤 @{user['username'] or 'N/A'}
📛 {user['first_name'] or 'N/A'}
📅 Joined: {user['join_date']}
💰 Points: {user['points']}
⭐ Premium: {'✅' if premium else '❌'}
📊 Usage: {user['usage_count']} requests
🚫 Banned: {'Yes' if banned else 'No'}

👥 Referral Link:
<code>https://t.me/{bot.get_me().username}?start={user_id}</code>
"""
    else:
        text = "❌ User not found."
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)
