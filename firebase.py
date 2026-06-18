# firebase.py
import telebot
from config import BOT_TOKEN
from buttons import back_button, main_menu

bot = telebot.TeleBot(BOT_TOKEN)

@bot.callback_query_handler(func=lambda call: call.data == "menu:firebase")
def firebase_menu(call):
    bot.edit_message_text("🔥 <b>Firebase Extractor</b>\n\nSend Firebase URL:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)
    # Register next handler for URL input
    bot.register_next_step_handler(call.message, handle_firebase_url)

def handle_firebase_url(message):
    user_id = message.from_user.id
    url = message.text.strip()
    db = None  # we'll import inside
    from database import Database
    db = Database()
    db.log_feature(user_id, "firebase_extractor", url)
    bot.send_message(user_id, f"🔥 Firebase extraction initiated for {url}\n(Feature coming soon)", reply_markup=main_menu())