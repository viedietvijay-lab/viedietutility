# premium.py
import telebot
import time, json, hmac, hashlib
import requests
from config import BOT_TOKEN, PREMIUM_PRICE, PAYMENT_API_URL, PAYMENT_SECRET_KEY
from database import Database
from points_manager import PointsManager
from buttons import main_menu, back_button

from bot_instance import bot
db = Database()
pm = PointsManager()

@bot.callback_query_handler(func=lambda call: call.data == "menu:premium")
def premium_menu(call):
    user_id = call.from_user.id
    is_prem = db.is_premium(user_id)
    text = f"⭐ <b>Premium Plan</b>\n\nPrice: ₹{PREMIUM_PRICE} (one-time)\nBenefits:\n• Unlimited tools\n• No point deduction\n• All features unlocked\n\nStatus: {'✅ Active' if is_prem else '❌ Inactive'}"
    buttons = []
    if not is_prem:
        buttons.append([("💳 Buy Premium (₹49)", "premium:buy", "success")])
    buttons.append([("◀️ Back", "menu:main", "primary")])
    bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "premium:buy")
def buy_premium(call):
    user_id = call.from_user.id
    if db.is_premium(user_id):
        bot.answer_callback_query(call.id, "⭐ Already premium!", show_alert=True)
        return
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return
    # Create order via payment gateway
    order = create_payment_order(user_id)
    if order and order.get('payment_link'):
        # Send payment link
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("💳 Pay Now", url=order['payment_link']),
            types.InlineKeyboardButton("🔁 Check Payment", callback_data=f"premium:check_payment:{order['order_id']}", style="primary"),
            types.InlineKeyboardButton("◀️ Back", callback_data="menu:main", style="primary")
        )
        bot.send_message(user_id, f"💳 Click below to pay ₹{PREMIUM_PRICE}\nOrder ID: <code>{order['order_id']}</code>", reply_markup=kb)
        if order.get('qr_code'):
            try:
                bot.send_photo(user_id, order['qr_code'], caption="Scan to pay")
            except: pass
    else:
        bot.send_message(user_id, "❌ Payment initiation failed. Try again later.")
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("premium:check_payment:"))
def check_payment(call):
    user_id = call.from_user.id
    order_id = call.data.split(":")[2]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT status FROM transactions WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0] == "success":
        db.set_premium(user_id, 30)
        bot.edit_message_text("✅ <b>Payment Verified!</b>\n\n🎉 Your Premium plan is now active!",
                              chat_id=call.message.chat.id, message_id=call.message.message_id,
                              reply_markup=main_menu())
    elif row and row[0] == "pending":
        bot.answer_callback_query(call.id, "⏳ Payment pending. Complete payment and try again.", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "❌ Order not found.", show_alert=True)

def create_payment_order(user_id):
    try:
        payload = {
            "amount": PREMIUM_PRICE,
            "currency": "INR",
            "receipt": f"order_{user_id}_{int(time.time())}",
            "notes": {"user_id": user_id}
        }
        headers = {"Authorization": f"Bearer {PAYMENT_SECRET_KEY}", "Content-Type": "application/json"}
        resp = requests.post(PAYMENT_API_URL, json=payload, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            db.add_transaction(user_id, data.get('order_id'), "", PREMIUM_PRICE, "pending")
            return {'order_id': data.get('order_id'), 'payment_link': data.get('payment_link'), 'qr_code': data.get('qr_code')}
    except Exception as e:
        pass
    return None

# Webhook handler (if you run a separate Flask server)
def handle_payment_webhook(request_data):
    try:
        data = json.loads(request_data)
        order_id = data.get('order_id')
        payment_id = data.get('payment_id')
        signature = data.get('signature')
        # Verify signature (example)
        expected = hmac.new(PAYMENT_SECRET_KEY.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
        if expected == signature and data.get('status') == 'success':
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT user_id FROM transactions WHERE order_id = ?", (order_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                user_id = row[0]
                db.set_premium(user_id, 30)
                db.update_transaction(order_id, payment_id, "success")
                # Notify user
                try:
                    bot.send_message(user_id, "✅ Payment successful! Premium activated.")
                except: pass
                return {"status": "success"}
        return {"status": "failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
