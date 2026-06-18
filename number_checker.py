# number_checker.py
import telebot
import requests
import re
import time
import random
from telebot import types
from bot_instance import bot
from config import TOOL_COST, INDIA_COORDINATES
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu, create_colored_keyboard

db = Database()
pm = PointsManager()

# ==================== HELPERS ====================

def get_random_coords():
    """Return random India coordinates"""
    return random.choice(INDIA_COORDINATES)

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return random.choice(user_agents)

def safe_request(method, url, **kwargs):
    """Wrapper for requests with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 1.5))
            kwargs['timeout'] = 20
            if 'headers' in kwargs:
                kwargs['headers']['User-Agent'] = get_random_user_agent()
            response = requests.request(method, url, **kwargs)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)
    return None

# ==================== FLIPKART CHECKER ====================

def flipkart_check(phone):
    try:
        get_random_coords()
        url = "https://1.rome.api.flipkart.com:443/api/6/user/signup/status"
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Referer": "https://www.flipkart.com/",
            "Origin": "https://www.flipkart.com",
            "Connection": "close"
        }
        payload = {"loginId": ["+91" + phone], "supportAllStates": True}
        
        response = safe_request("POST", url, headers=headers, json=payload)
        if not response:
            return False, "⚠️ API request failed (timeout). Please try again."
        
        if response.status_code == 200:
            data = response.json()
            resp_block = data.get('RESPONSE', {})
            user_details = resp_block.get('userDetails', {})
            status = user_details.get("+91" + phone)
            
            if status == "VERIFIED":
                return True, "✅ Registered on Flipkart"
            elif status == "GUEST":
                return False, "❌ Not Registered on Flipkart"
            else:
                return False, f"⚠️ Unknown status: {status}"
        else:
            return False, f"⚠️ API Error (HTTP {response.status_code})"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:80]}"

# ==================== BREVISTAY CHECKER ====================

def brevistay_check(phone):
    try:
        get_random_coords()
        url = "https://www.brevistay.com/cst/app-api/login"
        headers = {
            "accept": "application/json",
            "brevi-channel": "DESKTOP_WEB",
            "content-type": "application/json",
            "origin": "https://www.brevistay.com",
            "referer": "https://www.brevistay.com/login",
            "user-agent": get_random_user_agent()
        }
        payload = {"is_otp": 1, "is_password": 0, "mobile": phone}
        
        response = safe_request("POST", url, headers=headers, json=payload)
        if not response:
            return False, "⚠️ API request failed (timeout). Please try again."
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "SUCCESS":
                is_registered = data.get("is_user_registered") == "1"
                if is_registered:
                    return True, "✅ Registered on Brevistay"
                else:
                    return False, "❌ Not Registered on Brevistay"
            else:
                return False, f"⚠️ API Error: {data.get('status', 'Unknown')}"
        else:
            return False, f"⚠️ HTTP Error: {response.status_code}"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:80]}"

# ==================== SWIGGY CHECKER ====================

def swiggy_check(phone):
    try:
        get_random_coords()
        url = "https://www.swiggy.com/mapi/auth/signin-check"
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": "https://www.swiggy.com",
            "Referer": "https://www.swiggy.com/",
            "x-app-version": "2025.1.0"
        }
        payload = {"phoneNumber": phone}
        
        response = safe_request("POST", url, headers=headers, json=payload)
        if not response:
            return False, "⚠️ API request failed (timeout). Please try again."
        
        if response.status_code == 200:
            data = response.json()
            if data.get("statusCode") == 0:
                user_data = data.get("data", {})
                is_registered = user_data.get("registered", False)
                if is_registered:
                    return True, "✅ Registered on Swiggy"
                else:
                    return False, "❌ Not Registered on Swiggy"
            else:
                return False, f"⚠️ API Error: {data.get('statusCode', 'Unknown')}"
        else:
            return False, f"⚠️ HTTP Error: {response.status_code}"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:80]}"

# ==================== BOT HANDLERS ====================

@bot.callback_query_handler(func=lambda call: call.data == "menu:num_checker")
def num_checker_menu(call):
    buttons = [
        [("📱 Flipkart", "service:flipkart", "primary")],
        [("📱 Brevistay", "service:brevistay", "success")],
        [("📱 Swiggy", "service:swiggy", "danger")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    bot.edit_message_text(
        "🔢 <b>Number Checker</b>\n\n"
        f"💰 Cost: {TOOL_COST} point per check\n"
        "⭐ Premium: Free\n\n"
        "Select a platform:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=create_colored_keyboard(buttons)
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("service:"))
def service_selected(call):
    user_id = call.from_user.id
    service = call.data.split(":")[1]
    
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return
    
    pending_phone[user_id] = service
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("◀️ Back", callback_data="menu:num_checker", style="danger"))
    
    bot.edit_message_text(
        f"📱 <b>{service.title()} Checker</b>\n\n"
        f"Send 10-digit phone number (without +91):\n\n"
        f"📝 <b>Example:</b> <code>9826621729</code>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

pending_phone = {}

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and len(m.text) == 10 and m.from_user.id in pending_phone)
def handle_number_input(message):
    user_id = message.from_user.id
    service = pending_phone.pop(user_id, None)
    if not service:
        return
    
    if not pm.can_use_tool(user_id):
        bot.send_message(user_id, f"❌ Insufficient points! Need {TOOL_COST} point.", reply_markup=main_menu())
        return
    
    phone = message.text
    processing = bot.send_message(user_id, "🔍 Checking... Please wait ⏳")
    
    # Perform check
    if service == "flipkart":
        registered, msg = flipkart_check(phone)
    elif service == "brevistay":
        registered, msg = brevistay_check(phone)
    elif service == "swiggy":
        registered, msg = swiggy_check(phone)
    else:
        registered, msg = False, "❌ Unknown service"
    
    # Deduct points if check was performed (or we can deduct before)
    # If check fails due to error, we can refund points later
    pm.use_tool(user_id)
    db.log_feature(user_id, f"number_checker:{service}", phone)
    
    result_text = "✅ Registered" if registered else "❌ Not Registered"
    bot.edit_message_text(
        f"📱 <b>{service.title()} Check Result</b>\n\n"
        f"📱 Number: <code>{phone}</code>\n"
        f"📊 Status: <b>{result_text}</b>\n\n"
        f"{msg}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Powered By Viediet Utility</i>",
        chat_id=user_id,
        message_id=processing.message_id,
        parse_mode='HTML'
    )
