# main.py
import telebot
import time
from config import BOT_TOKEN, ADMIN_IDS
from database import Database
from force_join import check_force_join, force_join_keyboard
from buttons import main_menu
from admin import admin_panel, admin_actions
from number_checker import *
from downloaders import *
from temp_mail import *
from upi import *
from hash_tools import *
from image_to_pdf import *
from bypass import *
from firebase import *
from profile import *
from support import *
from premium import *

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()

# ===== Decorators =====
def check_ban(func):
    def wrapper(message):
        banned, _ = db.is_banned(message.from_user.id)
        if banned:
            bot.send_message(message.chat.id, "🚫 You are banned!")
            return
        return func(message)
    return wrapper

def require_join(func):
    def wrapper(message):
        if not check_force_join(message.from_user.id):
            bot.send_message(message.chat.id, "🔒 Please join our channel first!", reply_markup=force_join_keyboard())
            return
        return func(message)
    return wrapper

def require_join_callback(func):
    def wrapper(call):
        if not check_force_join(call.from_user.id):
            bot.answer_callback_query(call.id, "🔒 Join channel first!", show_alert=True)
            return
        return func(call)
    return wrapper

# ===== Start Handler =====
@bot.message_handler(commands=['start'])
@check_ban
@require_join
def send_welcome(message):
    user_id = message.from_user.id
    args = message.text.split()
    referred_by = int(args[1]) if len(args) > 1 and args[1].isdigit() else None
    db.register_user(user_id, message.from_user.username, message.from_user.first_name, message.from_user.last_name, referred_by)
    user = db.get_user(user_id)
    points = user['points'] if user else 0
    premium = db.is_premium(user_id)
    welcome = f"""
🌟 <b>Welcome to Viediet Utility!</b>

🤖 Your all-in-one Telegram bot

━━━━━━━━━━━━━━━━━━━━
💰 Points: {points}
⭐ Premium: {'✅ Active' if premium else '❌ Inactive'}
━━━━━━━━━━━━━━━━━━━━

⚡ <b>How it works:</b>
• Each tool use costs <b>1 point</b>
• Refer a friend → <b>+8 points</b>
• Premium → <b>Unlimited</b> access

👥 <b>Your Referral Link:</b>
<code>https://t.me/{bot.get_me().username}?start={user_id}</code>

━━━━━━━━━━━━━━━━━━━━
<i>Powered By Viediet Utility</i>
"""
    bot.send_message(user_id, welcome, reply_markup=main_menu())

# ===== Check Join Callback =====
@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if check_force_join(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Access Granted!", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Please join channel first!", show_alert=True)

# ===== Fallback =====
@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "❌ Use the menu buttons or /start.", reply_markup=main_menu())

# ===== Run =====
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════╗
║    ✦ VIEDIET UTILITY FINAL ✦     ║
║    All modules loaded             ║
╚═══════════════════════════════════╝
    """)
    # Register all handlers (already registered via imports)
    # admin panel handlers are already registered in admin.py
    # All other callbacks are registered in their respective files.
    # We just need to start polling.
    try:
        bot.infinity_polling(timeout=120, long_polling_timeout=120)
    except KeyboardInterrupt:
        print("👋 Stopped.")