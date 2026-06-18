# admin.py
import telebot
import time
import sqlite3
from telebot import types
from bot_instance import bot
from config import ADMIN_IDS, DB_PATH
from database import Database
from buttons import create_colored_keyboard, services_panel

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

# ==================== ADMIN ACTIONS ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin:"))
def admin_actions(call):
    user_id = call.from_user.id
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
        return
    
    action = call.data.split(":")[1]
    
    if action == "stats":
        total_users = db.get_user_count()
        banned_users = len(db.get_banned_users())
        text = f"📊 <b>Bot Statistics</b>\n\n👥 Total Users: {total_users}\n🚫 Banned Users: {banned_users}\n✅ Active Users: {total_users - banned_users}"
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if action == "banned":
        banned = db.get_banned_users()
        if not banned:
            text = "✅ No banned users."
        else:
            text = "🚫 <b>Banned Users</b>\n\n"
            for b in banned[:10]:
                text += f"• {b['user_id']} - {b['reason'] or 'No reason'}\n"
            if len(banned) > 10:
                text += f"\n... and {len(banned)-10} more"
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.answer_callback_query(call.id)
        return
    
    if action == "ban":
        bot.edit_message_text("🚫 <b>Ban User</b>\n\nSend user ID and reason:\n<code>123456789 Spam</code>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(call.message, handle_ban_input)
        bot.answer_callback_query(call.id)
        return
    
    if action == "unban":
        bot.edit_message_text("✅ <b>Unban User</b>\n\nSend user ID to unban:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(call.message, handle_unban_input)
        bot.answer_callback_query(call.id)
        return
    
    if action == "broadcast":
        bot.edit_message_text("📢 <b>Broadcast</b>\n\nSend your message:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(call.message, handle_broadcast)
        bot.answer_callback_query(call.id)
        return
    
    if action == "add_pts":
        bot.edit_message_text("💰 <b>Add Points</b>\n\nSend user ID and points:\n<code>123456789 10</code>", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(call.message, handle_add_points)
        bot.answer_callback_query(call.id)
        return
    
    if action == "premium":
        bot.edit_message_text("⭐ <b>Give Premium</b>\n\nSend user ID:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='HTML')
        bot.register_next_step_handler(call.message, handle_give_premium)
        bot.answer_callback_query(call.id)
        return
    
    bot.answer_callback_query(call.id, "❌ Unknown action", show_alert=True)

# ==================== HANDLER FUNCTIONS ====================

def handle_ban_input(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split(maxsplit=1)
        target = int(parts[0])
        reason = parts[1] if len(parts) > 1 else "No reason"
        db.ban_user(target, reason, user_id)
        bot.send_message(user_id, f"✅ Banned {target}")
    except:
        bot.send_message(user_id, "❌ Invalid format. Use: <code>USER_ID REASON</code>", parse_mode='HTML')

def handle_unban_input(message):
    user_id = message.from_user.id
    try:
        target = int(message.text.strip())
        db.unban_user(target)
        bot.send_message(user_id, f"✅ Unbanned {target}")
    except:
        bot.send_message(user_id, "❌ Invalid user ID.")

def handle_broadcast(message):
    user_id = message.from_user.id
    msg = message.text.strip()
    users = db.get_all_users()
    sent = 0
    for u in users:
        try:
            bot.send_message(u['user_id'], msg, parse_mode='HTML')
            sent += 1
            time.sleep(0.05)
        except:
            pass
    bot.send_message(user_id, f"✅ Broadcast sent to {sent} users.")

def handle_add_points(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split()
        target = int(parts[0])
        pts = int(parts[1])
        db.add_points(target, pts)
        bot.send_message(user_id, f"✅ Added {pts} points to {target}.")
    except:
        bot.send_message(user_id, "❌ Invalid format. Use: <code>USER_ID POINTS</code>", parse_mode='HTML')

def handle_give_premium(message):
    user_id = message.from_user.id
    try:
        target = int(message.text.strip())
        db.set_premium(target, 30)
        bot.send_message(user_id, f"✅ Premium given to {target} for 30 days.")
        bot.send_message(target, "🎉 <b>Premium Activated!</b>\n\nAdmin has activated your Premium plan for 30 days.", parse_mode='HTML')
    except:
        bot.send_message(user_id, "❌ Invalid user ID.")
