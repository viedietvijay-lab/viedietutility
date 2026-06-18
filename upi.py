# upi.py
import telebot
import qrcode
import os, time
from config import BOT_TOKEN, TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu

bot = telebot.TeleBot(BOT_TOKEN)
db = Database()
pm = PointsManager()

pending_upi = {}

@bot.callback_query_handler(func=lambda call: call.data == "menu:upi")
def upi_menu(call):
    user_id = call.from_user.id
    bot.edit_message_text("💳 <b>UPI QR Generator</b>\n\nSend your UPI ID (e.g., example@upi):",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    pending_upi[user_id] = True
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.text and '@' in m.text and m.from_user.id in pending_upi)
def handle_upi_input(message):
    user_id = message.from_user.id
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Need {TOOL_COST} point!", reply_markup=main_menu())
        del pending_upi[user_id]
        return
    upi_id = message.text.strip()
    if '@' not in upi_id:
        bot.send_message(user_id, "❌ Invalid UPI ID. Use example@upi", reply_markup=back_button())
        return
    pm.use_tool(user_id)
    upi_url = f"upi://pay?pa={upi_id}&pn=Viediet"
    qr = qrcode.QRCode(version=2, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = f"upi_{user_id}_{int(time.time())}.png"
    img.save(qr_path)
    with open(qr_path, 'rb') as f:
        bot.send_photo(user_id, f, caption=f"💳 UPI QR for {upi_id}")
    os.remove(qr_path)
    del pending_upi[user_id]