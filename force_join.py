# force_join.py
import telebot
from telebot import types
from config import BOT_TOKEN, FORCE_CHANNEL, FORCE_GROUP

bot = telebot.TeleBot(BOT_TOKEN)

def check_force_join(user_id):
    try:
        member = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def force_join_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_CHANNEL.lstrip('@')}"),
        types.InlineKeyboardButton("👥 Join Group", url=FORCE_GROUP),
        types.InlineKeyboardButton("✅ Check Join", callback_data="check_join", style="success")
    )
    return kb