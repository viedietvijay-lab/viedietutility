# premium.py
import telebot
import qrcode
import os
import time
import requests
import sqlite3
from telebot import types
from bot_instance import bot
from config import PREMIUM_PRICE, ADMIN_IDS, UPI_ID, PAYMENT_SECRET_KEY, DB_PATH
from database import Database
from points_manager import PointsManager
from buttons import main_menu, create_colored_keyboard

db = Database()
pm = PointsManager()

# ==================== VC GATEWAY PAYMENT STATUS ====================

def check_payment_status(order_id, amount):
    """
    Check payment status from VC Gateway.
    Uses the exact API call from your JavaScript code.
    """
    url = (
        "https://vcapi.vcstore.site/payment_api.php"
        f"?api_key={PAY735DE219C41F68FBD1172102}"
        f"&order_id={order_id}"
        f"&amount={amount}"
    )
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # The API returns status: "success", "pending", or "failed"
            return data.get("status", "pending")
        return "pending"
    except Exception as e:
        print(f"Status check error: {e}")
        return "pending"

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
        buttons.append([("💳 Buy Premium (₹2)", "premium:buy")])
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
    
    # Generate unique order ID (matching VC Gateway format)
    order_id = f"ORD{int(time.time() * 1000)}"   # e.g., ORD1781778122345
    amount = PREMIUM_PRICE
    
    # Store in database as pending
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
    
    # Generate QR code (using quickchart.io for consistency, or you can use local qrcode)
    import urllib.parse
    qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(upi_string)}"
    
    # Send QR as photo
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
    
    # Get amount from database
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT amount, status FROM transactions WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    
    if not row:
        bot.answer_callback_query(call.id, "❌ Order not found!", show_alert=True)
        return
    
    amount = row[0]
    current_status = row[1]
    
    if current_status == "success":
        bot.answer_callback_query(call.id, "✅ Already verified!", show_alert=True)
        return
    
    # Check with VC Gateway
    status = check_payment_status(order_id, amount)
    
    if status == "success":
        # Activate premium
        db.set_premium(user_id, 30)
        db.update_transaction(order_id, "", "success")
        bot.edit_message_text(
            "🎉 <b>Payment Confirmed!</b>\n\n"
            "Your Premium plan is now active for 30 days.\n"
            "Enjoy unlimited access to all tools!",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML',
            reply_markup=main_menu()
        )
        bot.answer_callback_query(call.id, "✅ Premium activated!", show_alert=True)
        
    elif status == "failed":
        # Payment not found – ask user to wait or contact admin
        bot.answer_callback_query(
            call.id,
            "❌ Payment not detected. If you paid, please wait 2-3 minutes and try again.\nIf the issue persists, contact admin.",
            show_alert=True
        )
        bot.send_message(
            user_id,
            "❌ <b>Payment not detected.</b>\n\n"
            "If you have paid, please wait a few minutes and click 'Check Payment' again.\n"
            "If the issue persists, contact admin with your Order ID:\n"
            f"<code>{order_id}</code>\n\n"
            "Admin: /givepremium <user_id>",
            parse_mode='HTML'
        )
        
    else:  # pending
        bot.answer_callback_query(
            call.id,
            "⏳ Payment pending. Please wait and try again in a few minutes.",
            show_alert=True
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
        bot.send_message(user_id, f"✅ Premium activated for {target} for 30 days.")
        bot.send_message(
            target,
            "🎉 <b>Premium Activated!</b>\n\n"
            "Admin has activated your Premium plan for 30 days.",
            parse_mode='HTML'
        )
    except:
        bot.send_message(user_id, "❌ Usage: <code>/givepremium &lt;user_id&gt;</code>", parse_mode='HTML')
