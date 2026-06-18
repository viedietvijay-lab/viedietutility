# number_checker.py
import telebot
import requests
import re
from telebot import types
from config import BOT_TOKEN, TOOL_COST, INDIA_COORDINATES
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu, create_colored_keyboard

from bot_instance import bot
db = Database()
pm = PointsManager()

# Helper to rotate coordinates
coord_idx = 0
def next_coord():
    global coord_idx
    c = INDIA_COORDINATES[coord_idx % len(INDIA_COORDINATES)]
    coord_idx += 1
    return c

# ----- Checker functions -----
def flipkart_check(phone):
    try:
        next_coord()
        url = "https://1.rome.api.flipkart.com:443/api/6/user/signup/status"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
            "Accept": "*/*", "Content-Type": "application/json", "Referer": "https://www.flipkart.com/",
            "Origin": "https://www.flipkart.com", "Connection": "close"
        }
        payload = {"loginId": ["+91"+phone], "supportAllStates": True}
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            status = data.get('RESPONSE', {}).get('userDetails', {}).get("+91"+phone)
            if status == "VERIFIED": return True, "✅ Registered on Flipkart"
            elif status == "GUEST": return False, "❌ Not Registered on Flipkart"
            else: return False, f"⚠️ Unknown status: {status}"
        return False, f"⚠️ API Error: {resp.status_code}"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:50]}"

def brevistay_check(phone):
    try:
        next_coord()
        url = "https://www.brevistay.com/cst/app-api/login"
        headers = {
            "accept": "application/json", "brevi-channel": "DESKTOP_WEB",
            "content-type": "application/json", "origin": "https://www.brevistay.com",
            "referer": "https://www.brevistay.com/login",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {"is_otp": 1, "is_password": 0, "mobile": phone}
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") == "SUCCESS":
                reg = data.get("is_user_registered") == "1"
                return (True, "✅ Registered on Brevistay") if reg else (False, "❌ Not Registered on Brevistay")
        return False, f"⚠️ API Error"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:50]}"

def swiggy_check(phone):
    try:
        next_coord()
        url = "https://www.swiggy.com/mapi/auth/signin-check"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json", "Content-Type": "application/json",
            "Origin": "https://www.swiggy.com", "Referer": "https://www.swiggy.com/",
            "x-app-version": "2025.1.0"
        }
        payload = {"phoneNumber": phone}
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("statusCode") == 0:
                reg = data.get("data", {}).get("registered", False)
                return (True, "✅ Registered on Swiggy") if reg else (False, "❌ Not Registered on Swiggy")
        return False, f"⚠️ API Error"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:50]}"

# ----- Callback handlers for menu -----
@bot.callback_query_handler(func=lambda call: call.data == "menu:num_checker")
def num_checker_menu(call):
    buttons = [
    [("🔵 Flipkart", "service:flipkart")],
    [("🟢 Brevistay", "service:brevistay")],
    [("🔴 Swiggy", "service:swiggy")],
]
    bot.edit_message_text("🔢 <b>Number Checker</b>\n\nSelect platform:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("service:"))
def service_selected(call):
    user_id = call.from_user.id
    service = call.data.split(":")[1]
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point! Refer a friend.", show_alert=True)
        return
    # Store service in a global dict (or use user_data)
    pending_phone[user_id] = service
    bot.edit_message_text(f"📱 <b>{service.title()} Checker</b>\n\nSend 10-digit number:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=back_button())
    bot.answer_callback_query(call.id)

# We'll define a global dict in main or here
pending_phone = {}

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and len(m.text)==10 and m.from_user.id in pending_phone)
def handle_number_input(message):
    user_id = message.from_user.id
    service = pending_phone.pop(user_id, None)
    if not service:
        return
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Need {TOOL_COST} point!", reply_markup=main_menu())
        return
    phone = message.text
    processing = bot.send_message(user_id, "🔍 Checking...")
    if service == "flipkart": reg, msg = flipkart_check(phone)
    elif service == "brevistay": reg, msg = brevistay_check(phone)
    elif service == "swiggy": reg, msg = swiggy_check(phone)
    else: reg, msg = False, "Unknown"
    pm.use_tool(user_id)
    result = "✅ Registered" if reg else "❌ Not Registered"
    bot.edit_message_text(f"📱 <b>{service.title()} Check</b>\n\nNumber: <code>{phone}</code>\nStatus: {result}\n\n{msg}",
                          chat_id=user_id, message_id=processing.message_id)
