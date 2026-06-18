# premium.py
import telebot
import qrcode
import os
import time
import requests
import sqlite3
import logging
from telebot import types
from bot_instance import bot
from config import PREMIUM_PRICE, ADMIN_IDS, UPI_ID, PAYMENT_SECRET_KEY, DB_PATH
from database import Database
from points_manager import PointsManager
from buttons import main_menu, create_colored_keyboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
pm = PointsManager()

# ==================== VC GATEWAY API CALL ====================

def check_payment_status(order_id, amount):
    """
    Calls VC Gateway payment_api.php exactly like the JS script.
    """
    url = (
        "https://vcapi.vcstore.site/payment_api.php"
        f"?api_key={PAY735DE219C41F68FBD1172102}"
        f"&order_id={order_id}"
        f"&amount={amount}"
    )
    logger.info(f"Checking payment: {url}")
    try:
        resp = requests.get(url, timeout=30)
        logger.info(f"Response: {resp.status_code} - {resp.text}")
        if resp.status_code == 200:
            data = resp.json()
            status = data.get("status", "pending")
            amount_credited = data.get("amount_credited", 0)
            return status, amount_credited
        return "pending", 0
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return "pending", 0

# ==================== PREMIUM MENU ====================

@bot.callback_query_handler(func=lambda call: call.data == "menu:premium")
def premium_menu(call):
    user_id = call.from_user.id
    is_prem = db.is_premium(user_id)
    text = (
        f"⭐ <b>Premium Plan</b>\n\n"
        f"Price: ₹{PREMIUM_PRICE} (one-time)\n\n"
        f"<b>Benefits:</b>\n"
        f"• Unlimited tools\n"
        f"• No point deduction\n"
        f"• All features unlocked\n\n"
        f"<b>Status:</b> {'✅ Active' if is_prem else '❌ Inactive'}"
    )
    buttons = []
    if not is_prem:
        buttons.append([("💳 Buy Premium (₹49)", "premium:buy")])
    buttons.append([("◀️ Back", "menu:main")])
    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=create_colored_keyboard(buttons)
    )
    bot.answer_callback_query(call.id)

# ==================== BUY PREMIUM ====================

@bot.callback_query_handler(func=lambda call: call.data == "premium:buy")
def buy_premium(call):
    user_id = call.from_user.id
    if db.is_premium(user_id):
        bot.answer_callback_query(call.id, "⭐ Already premium!", show_alert=True)
        return

    # Generate order ID (like ORD + timestamp)
    order_id = f"ORD{int(time.time() * 1000)}"
    amount = PREMIUM_PRICE

    # Save in DB
    db.add_transaction(user_id, order_id, "", amount, "pending")

    # Build UPI string exactly like VC Gateway script
    upi_string = (
        f"upi://pay?pa={UPI_ID}"
        f"&pn=VC%20Payment%20Gateway"
        f"&tid={order_id}"
        f"&tr={order_id}"
        f"&tn=VC%20Payment"
        f"&am={amount}"
        f"&cu=INR"
    )

    # Generate QR using quickchart.io (like the JS script)
    import urllib.parse
    qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(upi_string)}"

    bot.send_photo(
        user_id,
        qr_url,
        caption=(
            f"╔════════════════════╗\n"
            f"     💳 <b>VC PAYMENT GATEWAY</b>\n"
            f"╚════════════════════╝\n\n"
            f"💰 <b>Amount:</b> ₹{amount}\n"
            f"🆔 <b>Order ID:</b> {order_id}\n\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Complete the payment using the QR code above.\n"
            f"After successful payment, tap the button below.\n"
            f"━━━━━━━━━━━━━━━━━━"
        ),
        parse_mode='HTML'
    )

    # Check Payment button
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("✅ Check Payment", callback_data=f"premium:check:{order_id}"),
        types.InlineKeyboardButton("◀️ Back", callback_data="menu:main")
    )
    bot.send_message(user_id, "📌 Click after you complete the payment.", reply_markup=kb)
    bot.answer_callback_query(call.id)

# ==================== CHECK PAYMENT ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("premium:check:"))
def check_payment(call):
    user_id = call.from_user.id
    order_id = call.data.split(":")[2]

    # Immediate feedback
    bot.answer_callback_query(call.id, "⏳ Checking payment...")

    # Send processing message
    processing_msg = bot.send_message(user_id, "⏳ Checking payment status... Please wait.")

    # Get order details from DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT amount, status FROM transactions WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        bot.edit_message_text(
            "❌ Order not found. Please try again or contact admin.",
            chat_id=user_id,
            message_id=processing_msg.message_id
        )
        return

    amount = row[0]
    current_status = row[1]

    if current_status == "success":
        bot.edit_message_text(
            "✅ Already verified!\n\nYour Premium is active.",
            chat_id=user_id,
            message_id=processing_msg.message_id
        )
        return

    # Call VC Gateway API
    status, credited_amount = check_payment_status(order_id, amount)
    logger.info(f"Status: {status}, Credited: {credited_amount}")

    if status == "success":
        # Activate premium
        db.set_premium(user_id, 30)
        db.update_transaction(order_id, "", "success")
        bot.edit_message_text(
            "🎉 <b>Payment Confirmed!</b>\n\n"
            "Your Premium plan is now active for 30 days.\n"
            "Enjoy unlimited access to all tools!",
            chat_id=user_id,
            message_id=processing_msg.message_id,
            parse_mode='HTML'
        )
        bot.send_message(user_id, "✅ Premium activated!", reply_markup=main_menu())

    elif status == "failed":
        bot.edit_message_text(
            f"❌ <b>Payment not detected.</b>\n\n"
            f"Order ID: <code>{order_id}</code>\n\n"
            f"If you have paid, please wait 2-3 minutes and try again.\n"
            f"If the issue persists, contact admin.",
            chat_id=user_id,
            message_id=processing_msg.message_id,
            parse_mode='HTML'
        )

    else:  # pending
        bot.edit_message_text(
            f"⏳ <b>Payment pending.</b>\n\n"
            f"We are still waiting for confirmation.\n"
            f"Please try again in a few minutes.",
            chat_id=user_id,
            message_id=processing_msg.message_id,
            parse_mode='HTML'
        )

# ==================== ADMIN: MANUAL PREMIUM ====================

@bot.message_handler(commands=['givepremium'])
def give_premium_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        parts = message.text.split()
        target = int(parts[1])
        db.set_premium(target, 30)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE transactions SET status='success' WHERE user_id=?", (target,))
        conn.commit()
        conn.close()
        bot.send_message(user_id, f"✅ Premium activated for {target} for 30 days.")
        bot.send_message(
            target,
            "🎉 <b>Premium Activated!</b>\n\nAdmin has activated your Premium plan for 30 days.",
            parse_mode='HTML'
        )
    except:
        bot.send_message(user_id, "❌ Usage: <code>/givepremium &lt;user_id&gt;</code>", parse_mode='HTML')
