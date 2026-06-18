# main.py
import telebot
import time
from bot_instance import bot
from config import ADMIN_IDS
from database import Database
from force_join import check_force_join, force_join_keyboard
from buttons import bottom_menu, services_panel, back_button, services_back_button, profile_menu, support_menu, orders_menu, track_menu, deposit_menu, refer_menu, next_page_menu
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

db = Database()

# ==================== NAVIGATION HISTORY ====================
# Store user navigation history
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

@bot.message_handler(func=lambda m: m.text == "📦 My Orders")
@check_ban
@require_join
def orders_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "orders:recent")
    bot.send_message(
        user_id,
        "📦 <b>My Orders</b>\n\nYour recent orders will appear here.",
        parse_mode='HTML',
        reply_markup=orders_menu()
    )

@bot.message_handler(func=lambda m: m.text == "📦 Track Order")
@check_ban
@require_join
def track_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "track:order")
    bot.send_message(
        user_id,
        "🔍 <b>Track Order</b>\n\nSend your order ID to track.",
        parse_mode='HTML',
        reply_markup=track_menu()
    )

@bot.message_handler(func=lambda m: m.text == "💰 Deposit")
@check_ban
@require_join
def deposit_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "deposit:start")
    bot.send_message(
        user_id,
        "💰 <b>Deposit</b>\n\nAdd funds to your account.",
        parse_mode='HTML',
        reply_markup=deposit_menu()
    )

@bot.message_handler(func=lambda m: m.text == "🔗 Refer")
@check_ban
@require_join
def refer_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "refer:link")
    user = db.get_user(user_id)
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
    bot.send_message(
        user_id,
        "🆘 <b>SUPPORT</b>\n\nNeed help or facing any issue?\n\nSupport: @vishalcodeverseowner\n\nClick the button below to contact support.",
        parse_mode='HTML',
        reply_markup=support_menu()
    )

@bot.message_handler(func=lambda m: m.text == "📋 Next Page")
@check_ban
@require_join
def next_page_handler(message):
    user_id = message.from_user.id
    push_nav(user_id, "settings:page")
    bot.send_message(
        user_id,
        "📋 <b>More Options</b>",
        parse_mode='HTML',
        reply_markup=next_page_menu()
    )

# ==================== BACK NAVIGATION ====================

@bot.callback_query_handler(func=lambda call: call.data == "menu:back")
@check_ban_callback
@require_join_callback
def handle_back(call):
    user_id = call.from_user.id
    prev_menu = pop_nav(user_id)
    
    # If no history, go to services
    if not prev_menu or prev_menu == "menu:services":
        services_panel_handler(call.message)
        return
    
    # Navigate based on previous menu
    if prev_menu.startswith("profile:"):
        profile_handler(call.message)
    elif prev_menu.startswith("support:"):
        support_handler(call.message)
    elif prev_menu.startswith("orders:"):
        orders_handler(call.message)
    elif prev_menu.startswith("track:"):
        track_handler(call.message)
    elif prev_menu.startswith("deposit:"):
        deposit_handler(call.message)
    elif prev_menu.startswith("refer:"):
        refer_handler(call.message)
    elif prev_menu.startswith("settings:"):
        next_page_handler(call.message)
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
    
    # Store current menu in history
    push_nav(user_id, f"menu:{menu}")
    
    # Map menu to handlers
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
    
    # Send processing message with back button
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

# ==================== CALLBACK HANDLERS FOR OTHER MENUS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("profile:"))
@check_ban_callback
def profile_actions(call):
    bot.answer_callback_query(call.id, "✅ Profile feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("support:"))
@check_ban_callback
def support_actions(call):
    bot.answer_callback_query(call.id, "✅ Support feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("orders:"))
@check_ban_callback
def orders_actions(call):
    bot.answer_callback_query(call.id, "✅ Orders feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("track:"))
@check_ban_callback
def track_actions(call):
    bot.answer_callback_query(call.id, "✅ Track feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("deposit:"))
@check_ban_callback
def deposit_actions(call):
    bot.answer_callback_query(call.id, "✅ Deposit feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("refer:"))
@check_ban_callback
def refer_actions(call):
    bot.answer_callback_query(call.id, "✅ Refer feature coming soon!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("settings:"))
@check_ban_callback
def settings_actions(call):
    bot.answer_callback_query(call.id, "✅ Settings feature coming soon!", show_alert=True)

# ===================== CHECK JOIN CALLBACK ====================

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
