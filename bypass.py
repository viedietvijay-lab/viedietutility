# bypass.py
import telebot
from config import BOT_TOKEN
from buttons import create_colored_keyboard, back_button

bot = telebot.TeleBot(BOT_TOKEN)

@bot.callback_query_handler(func=lambda call: call.data == "menu:bypass")
def bypass_menu(call):
    buttons = [
        [("🌀 Yoga Bypass", "bypass:yoga", "primary")],
        [("🌀 Brevistay Bypass", "bypass:brevistay", "success")],
        [("◀️ Back", "menu:main", "primary")]
    ]
    bot.edit_message_text("🔓 <b>Bypass Tools</b>",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("bypass:"))
def bypass_action(call):
    bot.answer_callback_query(call.id, "🔄 Bypass feature coming soon!", show_alert=True)