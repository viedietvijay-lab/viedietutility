# main.py
import telebot
import time
from bot_instance import bot
from config import ADMIN_IDS, REFERRAL_POINTS, SIGNUP_BONUS, FORCE_GROUP
from database import Database
from force_join import check_force_join, force_join_keyboard
from buttons import *
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
from premium import *   # contains buy_premium

db = Database()

# ==================== NAVIGATION HISTORY ====================
nav_history = {}

def push_nav(user_id, menu):
    if user_id not in nav_history:
        nav_history[user_id] = []
    nav_history[user_id].append(menu)

def pop_nav(user_id):
    if user_id in nav_history and nav_history[user_id]:
        return nav_history[user_id].pop()
    return "menu:services"

def clear_nav(user_id):
    if user_id in nav_history:
        nav_history[user_id] = []

# ==================== DECORATORS ====================
def check_ban(func):
    def wrapper(message):
        banned, _ = db.is_banned(message.from_user.id)
        if banned:
            bot.send_message(message.chat.id, "🚫 You are banned!")
            return
        return func(message)
    return wrapper

def check_ban_callback(func):
    def wrapper(call):
        banned, _ = db.is_banned(call.from_user.id)
        if banned:
            bot.answer_callback_query(call.id, "🚫 You are banned!", show_alert=True)
            return
        return func(call)
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

# ==================== START HANDLER ====================
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

📌 Select an option from the menu below.

<i>Powered By Viediet Utility</i>
"""
    
    clear_nav(user_id)
    bot.send_message(user_id, welcome, parse_mode='HTML', reply_markup=bottom_menu())

# ==================== BOTTOM MENU HANDLERS ====================

@bot.message_handler(func=lambda m: m.text == "🛠️ Services")
@check_ban
@require_join
def services_panel_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "menu:services")
    bot.send_message(
        user_id,
        "🛠️ <b>SERVICES PANEL</b>\n\nSelect your favorite platform below:",
        parse_mode='HTML',
        reply_markup=services_panel()
    )

@bot.message_handler(func=lambda m: m.text == "👤 Profile")
@check_ban
@require_join
def profile_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "profile:account")
    user = db.get_user(user_id)
    if user:
        banned, _ = db.is_banned(user_id)
        premium = db.is_premium(user_id)
        text = f"""
👤 <b>Your Profile</b>

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
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=profile_menu())

@bot.message_handler(func=lambda m: m.text == "🔗 Refer")
@check_ban
@require_join
def refer_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "refer:link")
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    text = f"""
🔗 <b>Referral Link</b>

<code>{link}</code>

✨ <b>Benefits:</b>
• Each referral → +{REFERRAL_POINTS} points
• First time user → +{SIGNUP_BONUS} bonus

Share this link with your friends!
"""
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=refer_menu())

@bot.message_handler(func=lambda m: m.text == "🆘 Support")
@check_ban
@require_join
def support_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "support:contact")
    text = f"""
🆘 <b>SUPPORT</b>

Need help or facing any issue?

👥 Join our support group:
{FORCE_GROUP}

Click the button below to join.
"""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("👥 Join Support Group", url=FORCE_GROUP, style="primary"))
    kb.add(types.InlineKeyboardButton("◀️ Back", callback_data="menu:back", style="danger"))
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "⭐ Premium")
@check_ban
@require_join
def premium_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "premium:status")
    is_prem = db.is_premium(user_id)
    text = f"""
⭐ <b>Premium Plan</b>

Price: ₹{PREMIUM_PRICE} (one-time)
Benefits:
• Unlimited tools
• No point deduction
• All features unlocked

Status: {'✅ Active' if is_prem else '❌ Inactive'}
"""
    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=premium_menu())

# ==================== BACK BUTTON HANDLER ====================

@bot.callback_query_handler(func=lambda call: call.data == "menu:back")
@check_ban_callback
@require_join_callback
def back_button_handler(call):
    user_id = call.from_user.id
    prev_menu = pop_nav(user_id)
    
    if not prev_menu or prev_menu == "menu:services":
        services_panel_handler(call.message)
    elif prev_menu.startswith("profile:"):
        profile_handler(call.message)
    elif prev_menu.startswith("support:"):
        support_handler(call.message)
    elif prev_menu.startswith("refer:"):
        refer_handler(call.message)
    elif prev_menu.startswith("premium:"):
        premium_handler(call.message)
    else:
        services_panel_handler(call.message)
    
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "menu:services")
@check_ban_callback
@require_join_callback
def back_to_services(call):
    user_id = call.from_user.id
    clear_nav(user_id)
    services_panel_handler(call.message)
    bot.answer_callback_query(call.id)

# ==================== SERVICES PANEL CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu:"))
@check_ban_callback
@require_join_callback
def services_navigation(call):
    user_id = call.from_user.id
    menu = call.data.split(":")[1]
    push_nav(user_id, f"menu:{menu}")
    
    menu_map = {
        "ai_tools": "🤖 AI Tools - Coming Soon!",
        "downloaders": "📥 Downloaders - Coming Soon!",
        "image_tools": "🖼️ Image Tools - Coming Soon!",
        "pdf_tools": "📄 PDF Tools - Coming Soon!",
        "web_tools": "🌐 Web Tools - Coming Soon!",
        "hash_tools": "🔐 Hash Tools - Coming Soon!",
        "finance_tools": "💰 Finance Tools - Coming Soon!",
        "num_checker": "🔢 Number Checker - Coming Soon!",
        "bypass": "🔓 Bypass Tools - Coming Soon!",
        "temp_mail": "📧 Temp Mail - Coming Soon!",
        "upi": "💳 UPI QR - Coming Soon!",
        "image": "🖼️ Image to PDF - Coming Soon!",
        "firebase": "🔥 Firebase - Coming Soon!"
    }
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("◀️ Back to Services", callback_data="menu:services", style="primary"))
    
    bot.edit_message_text(
        f"📌 <b>{menu.replace('_', ' ').title()}</b>\n\n{menu_map.get(menu, 'Feature coming soon!')}",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

# ==================== OTHER CALLBACKS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("profile:"))
@check_ban_callback
def profile_actions(call):
    bot.answer_callback_query(call.id, "✅ Profile feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("support:"))
@check_ban_callback
def support_actions(call):
    bot.answer_callback_query(call.id, "✅ Support feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("refer:"))
@check_ban_callback
def refer_actions(call):
    user_id = call.from_user.id
    action = call.data.split(":")[1]
    if action == "link":
        link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        bot.answer_callback_query(call.id, "📋 Copied to chat!")
        bot.send_message(user_id, f"🔗 Your referral link:\n<code>{link}</code>", parse_mode='HTML')
    elif action == "stats":
        bot.answer_callback_query(call.id, "📊 Referral stats coming soon!", show_alert=True)

# ==================== PREMIUM BUY HANDLER ====================

@bot.callback_query_handler(func=lambda call: call.data == "premium:buy")
@check_ban_callback
@require_join_callback
def premium_buy_handler(call):
    """Handle premium buy button – calls existing buy_premium from premium.py"""
    from premium import buy_premium
    buy_premium(call)

@bot.callback_query_handler(func=lambda call: call.data == "premium:status")
@check_ban_callback
def premium_status(call):
    user_id = call.from_user.id
    is_prem = db.is_premium(user_id)
    bot.answer_callback_query(call.id, f"Premium: {'✅ Active' if is_prem else '❌ Inactive'}", show_alert=True)

# ==================== CHECK JOIN ====================

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if check_force_join(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Access Granted!", show_alert=True)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Please join channel first!", show_alert=True)

# ==================== FALLBACK ====================

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "❌ Use the menu buttons below.",
        reply_markup=bottom_menu()
    )

# ==================== RUN ====================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════╗
║    ✦ VIEDIET UTILITY FINAL ✦     ║
║    Colored UI + Bottom Menu      ║
╚═══════════════════════════════════╝
    """)
    try:
        bot.infinity_polling(timeout=120, long_polling_timeout=120)
    except KeyboardInterrupt:
        print("👋 Stopped.")
