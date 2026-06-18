# admin.py
import telebot
from telebot import types
from config import BOT_TOKEN, ADMIN_IDS
from database import Database
from buttons import create_colored_keyboard, back_button, main_menu

bot = telebot.TeleBot(BOT_TOKEN)
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
        [("🔙 Back", "menu:main", "primary")]
    ]
    return create_colored_keyboard(buttons)

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        bot.send_message(user_id, "❌ Access Denied!")
        return
    bot.send_message(user_id, "👑 <b>Admin Panel</b>", parse_mode='HTML', reply_markup=admin_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin:"))
def admin_actions(call):
    user_id = call.from_user.id
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
        return
    action = call.data.split(":")[1]

    if action == "stats":
        total = db.get_user_count()
        banned = len(db.get_banned_users())
        bot.edit_message_text(f"📊 Stats\n👥 Users: {total}\n🚫 Banned: {banned}",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if action == "banned":
        banned = db.get_banned_users()
        text = "✅ No banned users." if not banned else "🚫 Banned:\n" + "\n".join([f"• {b['user_id']} - {b['reason']}" for b in banned[:10]])
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if action == "ban":
        bot.edit_message_text("🚫 Send user ID and reason:\n<code>123456789 Spam</code>",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, handle_ban_input)
        bot.answer_callback_query(call.id)
        return

    if action == "unban":
        bot.edit_message_text("✅ Send user ID to unban:",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, handle_unban_input)
        bot.answer_callback_query(call.id)
        return

    if action == "broadcast":
        bot.edit_message_text("📢 Send broadcast message:",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, handle_broadcast)
        bot.answer_callback_query(call.id)
        return

    if action == "add_pts":
        bot.edit_message_text("💰 Enter user ID and points to add:\n<code>123456789 10</code>",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, handle_add_points)
        bot.answer_callback_query(call.id)
        return

    if action == "premium":
        bot.edit_message_text("⭐ Enter user ID to give premium (30 days):",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, handle_give_premium)
        bot.answer_callback_query(call.id)
        return

    bot.answer_callback_query(call.id)

def handle_ban_input(message):
    user_id = message.from_user.id
    try:
        parts = message.text.split(maxsplit=1)
        target = int(parts[0])
        reason = parts[1] if len(parts) > 1 else "No reason"
        db.ban_user(target, reason, user_id)
        bot.send_message(user_id, f"✅ Banned {target}")
    except:
        bot.send_message(user_id, "❌ Invalid format.")

def handle_unban_input(message):
    user_id = message.from_user.id
    try:
        target = int(message.text.strip())
        db.unban_user(target)
        bot.send_message(user_id, f"✅ Unbanned {target}")
    except:
        bot.send_message(user_id, "❌ Invalid ID.")

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
        bot.send_message(user_id, "❌ Invalid format.")

def handle_give_premium(message):
    user_id = message.from_user.id
    try:
        target = int(message.text.strip())
        db.set_premium(target, 30)
        bot.send_message(user_id, f"✅ Premium given to {target} for 30 days.")
    except:
        bot.send_message(user_id, "❌ Invalid ID.")