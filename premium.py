# premium.py
import telebot
import qrcode
import os
import time
import requests
from telebot import types
from bot_instance import bot
from config import PREMIUM_PRICE, ADMIN_IDS, UPI_ID, PAYMENT_SECRET_KEY
from database import Database
from points_manager import PointsManager
from buttons import main_menu, create_colored_keyboard

db = Database()
pm = PointsManager()

# ==================== VC GATEWAY FUNCTIONS ====================

def check_payment_status(order_id, amount):
    """
    Check payment status from VC Gateway.
    """
    url = (
        "https://vcapi.vcstore.site/payment_api.php"
        f"?api_key={PAYMENT_SECRET_KEY}"
        f"&order_id={order_id}"
        f"&amount={amount}"
    )
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
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
    
    # Generate unique order ID
    order_id = f"ORD_{user_id}_{int(time.time())}"
    amount = PREMIUM_PRICE
    
    # Store in database as pending
    db.add_transaction(user_id, order_id, "", amount, "pending")
    
    # Generate UPI QR
    upi_url = f"upi://pay?pa={UPI_ID}&am={amount}&cu=INR&tn=Premium"
    qr = qrcode.QRCode(version=2, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = f"premium_{user_id}_{int(time.time())}.png"
    img.save(qr_path)
    
    # Send QR
    with open(qr_path, 'rb') as f:
        bot.send_photo(
            user_id,
            f,
            caption=(
                f"💳 <b>Scan to pay ₹{amount}</b>\n\n"
                f"🏦 <b>UPI:</b> <code>{UPI_ID}</code>\n"
                f"🆔 <b>Order ID:</b> <code>{order_id}</code>\n\n"
                f"After payment, click the button below to verify."
            ),
            parse_mode='HTML'
        )
    os.remove(qr_path)
    
    # Buttons: Check Payment + Back
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
    
    # Check status from VC Gateway
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
        bot.answer_callback_query(call.id, "❌ Payment failed. Please try again.", show_alert=True)
        
    else:  # pending
        bot.answer_callback_query(
            call.id, 
            "⏳ Payment not confirmed yet. Please wait a few minutes and try again.",
            show_alert=True
        )

# ==================== ADMIN: GIVE PREMIUM ====================

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
