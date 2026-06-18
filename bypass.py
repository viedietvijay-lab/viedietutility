# bypass.py
import telebot
import requests
import re
import random
import time
from bot_instance import bot
from config import TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import create_colored_keyboard, back_button, main_menu

db = Database()
pm = PointsManager()

# ==================== CONSTANTS ====================
# Brevistay API endpoints
BREVISTAY_BASE = "https://cst.brevistay.com"
BREVISTAY_LOGIN = f"{BREVISTAY_BASE}/app-api/login"
BREVISTAY_VERIFY = f"{BREVISTAY_BASE}/app-api/verify-user"

# Habit.Yoga API endpoints (from yogabite.py)
YOGA_REGISTER = "https://auth-service.habuild.in/public/user/v1/register-user"
YOGA_LOGIN = "https://auth-service.habuild.in/public/auth/v1/login"
YOGA_VERIFY = "https://auth-service.habuild.in/public/auth/v1/verify-otp"

# Name pools for random generation
FIRST_NAMES = ["Amit", "Rahul", "Priya", "Neha", "Rohan", "Anjali", "Vikas", "Pooja"]
LAST_NAMES = ["Sharma", "Verma", "Singh", "Kumar", "Gupta", "Patel", "Reddy", "Jain"]

# ==================== HELPER FUNCTIONS ====================
def brevistay_headers():
    return {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; Pixel 4 Build/RQ3A.210705.001)",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

def yoga_headers():
    return {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": "https://habit.yoga",
        "referer": "https://habit.yoga/",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
    }

def random_name():
    return random.choice(FIRST_NAMES) + " " + random.choice(LAST_NAMES)

# ==================== BYPASS MENU ====================
@bot.callback_query_handler(func=lambda call: call.data == "menu:bypass")
def bypass_menu(call):
    buttons = [
        [("🌀 Yoga Bypass", "bypass:yoga")],
        [("🌀 Brevistay Bypass", "bypass:brevistay")],
        [("◀️ Back", "menu:main")]
    ]
    bot.edit_message_text("🔓 <b>Bypass Tools</b>\n\nSelect a bypass option:", 
                          chat_id=call.message.chat.id, 
                          message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

# ==================== BYPASS ACTIONS ====================
pending_bypass = {}  # user_id -> {"type": "yoga"|"brevistay", "step": "phone"|"otp"|"ref", "data": {...}}

@bot.callback_query_handler(func=lambda call: call.data.startswith("bypass:"))
def bypass_action(call):
    user_id = call.from_user.id
    bypass_type = call.data.split(":")[1]
    
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return

    # Initialize pending data
    pending_bypass[user_id] = {
        "type": bypass_type,
        "step": "phone",
        "data": {}
    }

    # Ask for phone number
    if bypass_type == "yoga":
        msg = "📱 <b>Yoga Bypass</b>\n\nSend your 10-digit phone number (without +91):"
    else:
        msg = "📱 <b>Brevistay Bypass</b>\n\nSend your 10-digit phone number (without +91):"
    
    bot.edit_message_text(msg,
                          chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

# ==================== HANDLE PHONE INPUT ====================
@bot.message_handler(func=lambda m: m.from_user.id in pending_bypass and pending_bypass[m.from_user.id]["step"] == "phone")
def handle_bypass_phone(message):
    user_id = message.from_user.id
    phone = message.text.strip()
    if not phone.isdigit() or len(phone) != 10:
        bot.send_message(user_id, "❌ Invalid phone number. Enter 10 digits.", reply_markup=back_button())
        return

    pending_bypass[user_id]["data"]["phone"] = phone
    pending_bypass[user_id]["step"] = "otp"

    # Send OTP
    bypass_type = pending_bypass[user_id]["type"]
    if bypass_type == "yoga":
        # Use Habit.Yoga login API to send OTP
        # We need to generate device ID and session ID (random UUID)
        import uuid
        did = str(uuid.uuid4())
        sid = str(uuid.uuid4())
        payload = {
            "method": "phone_otp",
            "otpChannel": "sms",
            "phoneNumber": "+91" + phone,
            "sourceData": {"type": "portal", "utm_source": "web_app"},
            "experimentMetaInfo": {"deviceId": did, "sessionId": sid},
            "registerUser": False
        }
        try:
            resp = requests.post(YOGA_LOGIN, json=payload, headers=yoga_headers(), timeout=15)
            data = resp.json()
            if resp.status_code == 200 and data.get("message") == "OTP sent to your phone":
                ref_code = data.get("data", {}).get("refrence_code")
                if ref_code:
                    pending_bypass[user_id]["data"]["otp_ref"] = ref_code
                    pending_bypass[user_id]["data"]["did"] = did
                    pending_bypass[user_id]["data"]["sid"] = sid
                    bot.send_message(user_id, "✅ OTP sent! Enter the 6-digit OTP:", reply_markup=back_button())
                else:
                    bot.send_message(user_id, "❌ OTP reference missing. Try again.", reply_markup=main_menu())
                    del pending_bypass[user_id]
            else:
                bot.send_message(user_id, f"❌ Failed to send OTP: {data.get('message', 'Unknown error')}", reply_markup=main_menu())
                del pending_bypass[user_id]
        except Exception as e:
            bot.send_message(user_id, f"❌ Error: {str(e)[:100]}", reply_markup=main_menu())
            del pending_bypass[user_id]

    else:  # Brevistay
        payload = {"is_otp": 1, "is_password": 0, "mobile": int(phone)}
        try:
            resp = requests.post(BREVISTAY_LOGIN, json=payload, headers=brevistay_headers(), timeout=15)
            data = resp.json()
            if data.get("is_otp_sent") == 1:
                bot.send_message(user_id, "✅ OTP sent! Enter the 6-digit OTP:", reply_markup=back_button())
            else:
                bot.send_message(user_id, "❌ Failed to send OTP. Try again.", reply_markup=main_menu())
                del pending_bypass[user_id]
        except Exception as e:
            bot.send_message(user_id, f"❌ Error: {str(e)[:100]}", reply_markup=main_menu())
            del pending_bypass[user_id]

# ==================== HANDLE OTP INPUT ====================
@bot.message_handler(func=lambda m: m.from_user.id in pending_bypass and pending_bypass[m.from_user.id]["step"] == "otp")
def handle_bypass_otp(message):
    user_id = message.from_user.id
    otp = message.text.strip()
    if not otp.isdigit() or len(otp) != 6:
        bot.send_message(user_id, "❌ Enter a valid 6-digit OTP.", reply_markup=back_button())
        return

    pending_bypass[user_id]["data"]["otp"] = otp
    bypass_type = pending_bypass[user_id]["type"]

    if bypass_type == "yoga":
        # Verify OTP
        ref = pending_bypass[user_id]["data"].get("otp_ref")
        phone = pending_bypass[user_id]["data"]["phone"]
        did = pending_bypass[user_id]["data"]["did"]
        sid = pending_bypass[user_id]["data"]["sid"]
        payload = {
            "phone": "+91" + phone,
            "reference_code": ref,
            "otp": otp,
            "experimentMetaInfo": {"deviceId": did, "sessionId": sid},
            "registerUser": False
        }
        try:
            resp = requests.post(YOGA_VERIFY, json=payload, headers=yoga_headers(), timeout=15)
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "success":
                # Now register user with referral code (we'll use a default or ask for referral code)
                # For simplicity, we'll ask for referral code
                pending_bypass[user_id]["step"] = "ref"
                bot.send_message(user_id, "✅ OTP verified! Now send your Habit.Yoga referral code (or 'skip'):", reply_markup=back_button())
            else:
                bot.send_message(user_id, "❌ OTP verification failed. Try again.", reply_markup=main_menu())
                del pending_bypass[user_id]
        except Exception as e:
            bot.send_message(user_id, f"❌ Error: {str(e)[:100]}", reply_markup=main_menu())
            del pending_bypass[user_id]

    else:  # Brevistay
        # OTP verified, now we need to create account with referral code
        pending_bypass[user_id]["step"] = "ref"
        bot.send_message(user_id, "✅ OTP verified! Now send your Brevistay referral code (or 'skip'):", reply_markup=back_button())

# ==================== HANDLE REFERRAL CODE INPUT ====================
@bot.message_handler(func=lambda m: m.from_user.id in pending_bypass and pending_bypass[m.from_user.id]["step"] == "ref")
def handle_bypass_ref(message):
    user_id = message.from_user.id
    ref_code = message.text.strip()
    if ref_code.lower() == "skip":
        ref_code = ""

    bypass_type = pending_bypass[user_id]["type"]
    phone = pending_bypass[user_id]["data"]["phone"]
    otp = pending_bypass[user_id]["data"]["otp"]

    if bypass_type == "yoga":
        # Complete registration on Habit.Yoga
        name = random_name()
        did = pending_bypass[user_id]["data"]["did"]
        sid = pending_bypass[user_id]["data"]["sid"]
        payload = {
            "name": name,
            "phoneNumber": "+91" + phone,
            "referredBy": ref_code,
            "sourceData": {"type": "Referral", "refererurl": "", "timezone": "Asia/Kolkata"},
            "experimentMetaInfo": {"deviceId": did, "sessionId": sid}
        }
        try:
            resp = requests.post(YOGA_REGISTER, json=payload, headers={**yoga_headers(), "authorization": "Bearer"}, timeout=15)
            data = resp.json()
            if resp.status_code == 201:
                # Deduct points and log
                pm.use_tool(user_id)
                db.log_feature(user_id, "yoga_bypass", f"phone:{phone}, ref:{ref_code}")
                bot.send_message(user_id, f"✅ <b>Yoga Bypass Successful!</b>\n\nAccount created for {name}\nPhone: +91{phone}\nReferral Code: {ref_code or 'None'}", parse_mode='HTML', reply_markup=main_menu())
            else:
                bot.send_message(user_id, f"❌ Registration failed: {data.get('message', 'Unknown error')}", reply_markup=main_menu())
        except Exception as e:
            bot.send_message(user_id, f"❌ Error: {str(e)[:100]}", reply_markup=main_menu())
        del pending_bypass[user_id]

    else:  # Brevistay
        # Complete Brevistay registration
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        email = f"{fname.lower()}.{lname.lower()}@gmail.com"
        payload = {
            "channel": "MOBILE",
            "email": email,
            "is_otp": 1,
            "is_password": 0,
            "lastName": lname,
            "mobile": int(phone),
            "name": fname,
            "otp": int(otp),
            "password": "xxxxx",
            "ref_code": ref_code,
            "age": random.randint(20, 35),
            "gender": random.choice(["MALE", "FEMALE"])
        }
        try:
            resp = requests.post(BREVISTAY_VERIFY, json=payload, headers=brevistay_headers(), timeout=15)
            data = resp.json()
            if data.get("status") == "SUCCESS":
                pm.use_tool(user_id)
                db.log_feature(user_id, "brevistay_bypass", f"phone:{phone}, ref:{ref_code}")
                bot.send_message(user_id, f"✅ <b>Brevistay Bypass Successful!</b>\n\nAccount created for {fname} {lname}\nEmail: {email}\nReferral Code: {data.get('user_referral_code', 'N/A')}", parse_mode='HTML', reply_markup=main_menu())
            else:
                bot.send_message(user_id, f"❌ Registration failed: {data.get('msg', 'Unknown error')}", reply_markup=main_menu())
        except Exception as e:
            bot.send_message(user_id, f"❌ Error: {str(e)[:100]}", reply_markup=main_menu())
        del pending_bypass[user_id]

# ==================== CANCEL ====================
@bot.message_handler(commands=['cancel'])
def cancel_bypass(message):
    user_id = message.from_user.id
    if user_id in pending_bypass:
        del pending_bypass[user_id]
        bot.send_message(user_id, "↩️ Bypass cancelled.", reply_markup=main_menu())
