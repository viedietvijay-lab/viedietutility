# admin.py
import telebot
import time
from telebot import types
from bot_instance import bot
from config import ADMIN_IDS
from database import Database
from buttons import create_colored_keyboard, back_button   # ✅ Remove main_menu

db = Database()

def admin_menu():
    buttons = [
        [("📊 Stats", "admin:stats", "primary")],
        [("📢 Broadcast", "admin:broadcast", "warning")],
        [("🚫 Ban", "admin:ban", "danger")],
        [("✅ Unban", "admin:unban", "success")],
        [("📋 Banned List", "admin:banned", "warning")],
        [("💰 Add Points", "admin:add_pts", "success")],
        [("⭐ Give Premium", "admin:premium", "primary")],
        [("🔙 Back to Services", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "❌ Access Denied!")
        return
    bot.send_message(user_id, "👑 <b>Admin Panel</b>", parse_mode='HTML', reply_markup=admin_menu())

# ... rest of admin.py remains same (admin_actions etc.)
