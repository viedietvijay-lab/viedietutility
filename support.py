# support.py
import telebot
from config import BOT_TOKEN, ADMIN_IDS
from database import Database
from buttons import create_colored_keyboard, back_button, main_menu

from bot_instance import bot
db = Database()

pending_contact = {}
pending_bug = {}

@bot.callback_query_handler(func=lambda call: call.data == "menu:support")
def support_menu(call):
    buttons = [
        [("📞 Contact Admin", "support:contact", "primary")],
        [("🐛 Report Bug", "support:bug", "danger")],
        [("❓ FAQ", "support:faq", "success")],
        [("◀️ Back", "menu:main", "primary")]
    ]
    bot.edit_message_text("🆘 <b>Help & Support</b>",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "support:contact")
def contact_admin(call):
    user_id = call.from_user.id
    pending_contact[user_id] = True
    bot.edit_message_text("📞 Send your message. Admin will reply.",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "support:bug")
def report_bug(call):
    user_id = call.from_user.id
    pending_bug[user_id] = True
    bot.edit_message_text("🐛 Describe the bug.",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "support:faq")
def faq(call):
    faq = """
❓ <b>FAQ</b>

Q: How to get points?
A: Refer a friend → +8 points

Q: How much does a tool cost?
A: 1 point per use (or free with Premium)

Q: What is Premium?
A: ₹49 for unlimited access

Q: How to contact admin?
A: Use "Contact Admin"
"""
    bot.edit_message_text(faq, chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.from_user.id in pending_contact)
def handle_contact(message):
    user_id = message.from_user.id
    msg = message.text
    db.log_feature(user_id, "contact_admin", msg)
    for admin in ADMIN_IDS:
        try:
            bot.send_message(admin, f"📞 Contact from @{message.from_user.username or 'N/A'} (ID: {user_id}):\n{msg}")
        except: pass
    bot.send_message(user_id, "✅ Message sent to admin.", reply_markup=main_menu())
    del pending_contact[user_id]

@bot.message_handler(func=lambda m: m.from_user.id in pending_bug)
def handle_bug(message):
    user_id = message.from_user.id
    msg = message.text
    db.log_feature(user_id, "report_bug", msg)
    for admin in ADMIN_IDS:
        try:
            bot.send_message(admin, f"🐛 Bug report from @{message.from_user.username or 'N/A'} (ID: {user_id}):\n{msg}")
        except: pass
    bot.send_message(user_id, "✅ Bug reported.", reply_markup=main_menu())
    del pending_bug[user_id]
