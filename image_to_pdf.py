# image_to_pdf.py
import telebot
import os, time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from config import BOT_TOKEN, TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu

from bot_instance import bot
db = Database()
pm = PointsManager()

img_collection = {}

@bot.callback_query_handler(func=lambda call: call.data == "menu:image")
def image_menu(call):
    user_id = call.from_user.id
    img_collection[user_id] = []
    bot.edit_message_text("🖼️ <b>Image to PDF</b>\n\nSend images one by one. Type <b>/done</b> when finished.",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo'])
def handle_image_upload(message):
    user_id = message.from_user.id
    if user_id not in img_collection:
        return
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Need {TOOL_COST} point!", reply_markup=main_menu())
        return
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    path = f"img_{user_id}_{len(img_collection[user_id])}_{int(time.time())}.jpg"
    downloaded = bot.download_file(file_info.file_path)
    with open(path, 'wb') as f:
        f.write(downloaded)
    img_collection[user_id].append(path)
    bot.reply_to(message, f"✅ Image {len(img_collection[user_id])} added. Send more or type /done.")

@bot.message_handler(commands=['done'])
def done_pdf(message):
    user_id = message.from_user.id
    if user_id not in img_collection or not img_collection[user_id]:
        bot.send_message(user_id, "❌ No images to convert.")
        return
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Need {TOOL_COST} point!", reply_markup=main_menu())
        return
    processing = bot.send_message(user_id, "📄 Creating PDF...")
    pdf_path = images_to_pdf(img_collection[user_id], user_id)
    if pdf_path:
        pm.use_tool(user_id)
        with open(pdf_path, 'rb') as f:
            bot.send_document(user_id, f, caption=f"✅ PDF created with {len(img_collection[user_id])} pages.")
        os.remove(pdf_path)
    else:
        bot.send_message(user_id, "❌ Failed to create PDF.")
    for p in img_collection[user_id]:
        try: os.remove(p)
        except: pass
    del img_collection[user_id]
    bot.delete_message(user_id, processing.message_id)

def images_to_pdf(image_paths, user_id):
    try:
        pdf_path = f"output_{user_id}_{int(time.time())}.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        for img_path in image_paths:
            img = ImageReader(img_path)
            w, h = img.getSize()
            pw, ph = letter
            scale = min(pw/w, ph/h) * 0.9
            x = (pw - w*scale)/2
            y = (ph - h*scale)/2
            c.drawImage(img, x, y, w*scale, h*scale)
            c.showPage()
        c.save()
        return pdf_path
    except Exception as e:
        return None
