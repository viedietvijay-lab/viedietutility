# hash_tools.py
import telebot
import hashlib, base64
from config import BOT_TOKEN, TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu, create_colored_keyboard

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()
pm = PointsManager()

pending_hash = {}

@bot.callback_query_handler(func=lambda call: call.data == "menu:hash")
def hash_menu(call):
    buttons = [
        [("🔐 MD5", "hash_md5", "primary")],
        [("🔐 SHA1", "hash_sha1", "success")],
        [("🔐 SHA256", "hash_sha256", "warning")],
        [("🔐 Base64 Encode", "hash_b64enc", "primary")],
        [("🔐 Base64 Decode", "hash_b64dec", "danger")],
        [("◀️ Back", "menu:main", "primary")]
    ]
    bot.edit_message_text("🔐 <b>Hash Tools</b>\n\nSelect:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hash_"))
def hash_selected(call):
    user_id = call.from_user.id
    hash_type = call.data.split("_")[1]
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return
    pending_hash[user_id] = hash_type
    bot.edit_message_text(f"🔐 <b>{hash_type.upper()}</b>\n\nSend text to process:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.from_user.id in pending_hash)
def handle_hash_input(message):
    user_id = message.from_user.id
    hash_type = pending_hash.pop(user_id, None)
    if not hash_type:
        return
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Need {TOOL_COST} point!", reply_markup=main_menu())
        return
    text = message.text
    if hash_type == "md5": out = hashlib.md5(text.encode()).hexdigest()
    elif hash_type == "sha1": out = hashlib.sha1(text.encode()).hexdigest()
    elif hash_type == "sha256": out = hashlib.sha256(text.encode()).hexdigest()
    elif hash_type == "b64enc": out = base64.b64encode(text.encode()).decode()
    elif hash_type == "b64dec":
        try: out = base64.b64decode(text).decode()
        except: out = "❌ Invalid Base64"
    else: out = "Invalid"
    pm.use_tool(user_id)
    bot.send_message(user_id, f"🔐 <b>{hash_type.upper()}</b>\n\nInput: <code>{text}</code>\nOutput: <code>{out}</code>", reply_markup=main_menu())