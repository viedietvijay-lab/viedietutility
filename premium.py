# premium.py
import telebot
import qrcode
import os
import time
import threading
import requests
import json
from bot_instance import bot
from config import PREMIUM_PRICE, ADMIN_IDS, PAYMENT_SECRET_KEY, DB_PATH, BHARATPE2G0O0Q6W0S58415@unitype  # Add UPI_ID to config
from database import Database
from points_manager import PointsManager
from buttons import main_menu, create_colored_keyboard

db = Database()
pm = PointsManager()

# ==================== VC GATEWAY PAYMENT FUNCTIONS ====================

def create_payment_order(user_id):
    """
    Create a payment order using VC Gateway.
    We generate a UPI QR with the fixed UPI ID and amount.
    The order is stored in DB as pending.
    """
    try:
        order_id = f"ORD_{user_id}_{int(time.time())}"
        
        # Store order in database as pending
        db.add_transaction(user_id, order_id, "", PREMIUM_PRICE, "pending")
        
        # Generate UPI QR code for payment
        upi_url = f"upi://pay?pa={UPI_ID}&am={PREMIUM_PRICE}&cu=INR&tn=Premium"
        
        qr = qrcode.QRCode(version=2, box_size=10, border=4)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = f"premium_{user_id}_{int(time.time())}.png"
        img.save(qr_path)
        
        return {
            "order_id": order_id,
            "qr_code": qr_path,
            "upi_id": UPI_ID,
            "amount": PREMIUM_PRICE
        }
    except Exception as e:
        print(f"Order creation error: {e}")
        return None

def check_order_status(order_id, amount):
    """
    Check payment status from VC Gateway.
    Uses the exact API call from your JavaScript code.
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
            # The API returns status like "success", "pending", or "failed"
            status = data.get("status", "pending")
            return status
        else:
            print(f"Status check HTTP error: {resp.status_code}")
            return "pending"
    except Exception as e:
        print(f"Status check error: {e}")
        return "pending"

def poll_payment(user_id, order_id, amount):
    """
    Background thread to auto-verify payment.
    Waits 30 seconds before first check, then polls every 5 seconds for up to 5 minutes.
    """
    # Wait 30 seconds to give user time to pay
    time.sleep(30)
    
    attempts = 0
    max_attempts = 54  # 54 * 5 seconds = 4.5 minutes (total ~5 min including initial wait)
    
    while attempts < max_attempts:
        time.sleep(5)
        attempts += 1
        
        status = check_order_status(order_id, amount)
        print(f"Poll {attempts}: status = {status}")
        
        if status == "success":
            # Activate premium
            db.set_premium(user_id, 30)
            db.update_transaction(order_id, "", "success")
            try:
                bot.send_message(
                    user_id,
                    "🎉 <b>Payment Confirmed!</b>\n\n"
                    "Your Premium plan is now active for 30 days.\n"
                    "Enjoy unlimited access to all tools!",
                    parse_mode='HTML'
                )
            except:
                pass
            # Cleanup QR file
            for f in os.listdir('.'):
                if f.startswith(f"premium_{user_id}") and f.endswith('.png'):
                    try:
                        os.remove(f)
                    except:
                        pass
            return
            
        elif status == "failed":
            try:
                bot.send_message(
                    user_id,
                    "❌ <b>Payment Failed</b>\n\n"
                    "Your payment was not successful. Please try again.",
                    parse_mode='HTML'
                )
            except:
                pass
            db.update_transaction(order_id, "", "failed")
            return
    
    # Timeout
    try:
        bot.send_message(
            user_id,
            f"⏳ <b>Payment Confirmation Timeout</b>\n\n"
            f"If you made the payment, please contact admin with your Order ID:\n"
            f"<code>{order_id}</code>",
            parse_mode='HTML'
        )
    except:
        pass

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
    
    # Create order
    order = create_payment_order(user_id)
    if not order:
        bot.answer_callback_query(call.id, "❌ Payment initiation failed. Try again.", show_alert=True)
        return
    
    # Send QR code
    with open(order["qr_code"], 'rb') as f:
        bot.send_photo(
            user_id,
            f,
            caption=(
                f"💳 <b>Scan to pay ₹{PREMIUM_PRICE}</b>\n\n"
                f"🏦 <b>UPI:</b> <code>{order['upi_id']}</code>\n"
                f"🆔 <b>Order ID:</b> <code>{order['order_id']}</code>\n\n"
                f"⏳ Payment will be <b>auto-verified</b> within 5 minutes.\n"
                f"Please complete the payment now."
            ),
            parse_mode='HTML'
        )
    
    # Schedule QR cleanup after 5 minutes
    threading.Timer(300, lambda: os.remove(order["qr_code"]) if os.path.exists(order["qr_code"]) else None).start()
    
    # Start background polling for payment confirmation
    thread = threading.Thread(
        target=poll_payment,
        args=(user_id, order["order_id"], order["amount"]),
        daemon=True
    )
    thread.start()
    
    bot.send_message(
        user_id,
        "⏳ <b>Waiting for payment confirmation...</b>\n\n"
        "You will be notified once your payment is verified.\n"
        "This may take up to 5 minutes.",
        parse_mode='HTML'
    )
    
    bot.answer_callback_query(call.id)

# ==================== ADMIN: GIVE PREMIUM MANUALLY ====================

@bot.message_handler(commands=['givepremium'])
def give_premium_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        target = int(parts[1])
        db.set_premium(target, 30)
        db.add_transaction(target, f"manual_{int(time.time())}", "admin", PREMIUM_PRICE, "success")
        bot.send_message(user_id, f"✅ Premium given to {target} for 30 days.")
        bot.send_message(target, "🎉 <b>Premium Activated!</b>\n\nAdmin has activated your Premium plan for 30 days.", parse_mode='HTML')
    except:
        bot.send_message(user_id, "❌ Usage: <code>/givepremium &lt;user_id&gt;</code>", parse_mode='HTML')

# ==================== ADMIN: CHECK PAYMENT STATUS ====================

@bot.message_handler(commands=['checkpayment'])
def check_payment_cmd(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        return
    
    try:
        parts = message.text.split()
        order_id = parts[1]
        amount = int(parts[2]) if len(parts) > 2 else PREMIUM_PRICE
        
        status = check_order_status(order_id, amount)
        bot.send_message(
            user_id,
            f"🔍 <b>Payment Status</b>\n\n"
            f"Order ID: <code>{order_id}</code>\n"
            f"Status: <b>{status.upper()}</b>",
            parse_mode='HTML'
        )
    except:
        bot.send_message(user_id, "❌ Usage: <code>/checkpayment &lt;order_id&gt; [amount]</code>", parse_mode='HTML')
