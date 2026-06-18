# number_checker.py
import telebot
import requests
import re
import time
import random
import json
from telebot import types
from bot_instance import bot
from config import TOOL_COST, INDIA_COORDINATES, ADMIN_IDS
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu, create_colored_keyboard

db = Database()
pm = PointsManager()

# Store pending phone checks
pending_phone = {}

# ==================== HELPERS ====================

def get_random_coords():
    return random.choice(INDIA_COORDINATES)

def get_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    return random.choice(agents)

def safe_request(method, url, **kwargs):
    max_retries = 2
    for attempt in range(max_retries):
        try:
            time.sleep(random.uniform(0.3, 1.0))
            if 'headers' in kwargs:
                kwargs['headers']['User-Agent'] = get_random_user_agent()
            else:
                kwargs['headers'] = {'User-Agent': get_random_user_agent()}
            kwargs['timeout'] = 20
            response = requests.request(method, url, **kwargs)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
    return None

# ==================== FLIPKART CHECKER (from your script) ====================

def flipkart_check(phone):
    try:
        get_random_coords()
        url = "https://1.rome.api.flipkart.com:443/api/6/user/signup/status"
        headers = {
            "User-Agent": get_random_user_agent(),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Referer": "https://www.flipkart.com/",
            "X-User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0 FKUA/website/42/website/Desktop",
            "Origin": "https://www.flipkart.com",
            "Connection": "close"
        }
        payload = {"loginId": ["+91" + phone], "supportAllStates": True}
        
        response = safe_request("POST", url, headers=headers, json=payload)
        if not response:
            return False, "⚠️ Request timeout. Try again."
        
        if response.status_code != 200:
            return False, f"⚠️ API Blocked (HTTP {response.status_code})"
        
        data = response.json()
        resp_block = data.get('RESPONSE', {})
        user_details = resp_block.get('userDetails', {})
        status = user_details.get("+91" + phone)
        
        if status == "VERIFIED":
            return True, "✅ Registered on Flipkart"
        elif status == "GUEST":
            return False, "❌ Not Registered on Flipkart"
        elif status is None:
            return False, "⚠️ Number not found in response"
        else:
            return False, f"⚠️ Unknown Status: {status}"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:80]}"

# ==================== BREVISTAY CHECKER (FIXED) ====================

def brevistay_check(number):
    try:
        url = "https://www.brevistay.com/cst/app-api/login"
        payload = {"is_otp": 1, "is_password": 0, "mobile": number}
        headers = {
            "Content-Type": "application/json",
            "brevi-channel": "DESKTOP_WEB",
            "brevi-channel-version": "41.0.0",
            "User-Agent": get_random_user_agent(),
            "Accept": "application/json",
            "Origin": "https://www.brevistay.com",
            "Referer": "https://www.brevistay.com/login"
        }
        response = safe_request("POST", url, json=payload, headers=headers)
        if not response:
            return False, "⚠️ Request timeout. Try again."
        
        if response.status_code != 200:
            return False, f"⚠️ API returned {response.status_code}"
        
        data = response.json()
        if data.get("status") == "SUCCESS" and data.get("is_user_registered") in ("1", 1, True):
            return True, "✅ Registered on Brevistay"
        else:
            return False, "❌ Not Registered on Brevistay"
    except Exception as e:
        return False, f"⚠️ Error: {str(e)[:80]}"


# ==================== SWIGGY CHECKER (FIXED) ====================

def get_swiggy_csrf():
    """Fetch CSRF token from Swiggy homepage"""
    try:
        url = "https://www.swiggy.com/"
        headers = {"User-Agent": get_random_user_agent()}
        resp = requests.get(url, headers=headers, timeout=15)
        # Extract CSRF token from HTML or cookie
        # Usually Swiggy sets a cookie named '_csrf' or embeds in meta tag.
        # For simplicity, we try to get from cookie:
        csrf = resp.cookies.get("_csrf")
        if csrf:
            return csrf
        # Alternatively, parse from HTML meta tag (if needed)
        # For now, fallback: try to get from a known pattern in HTML
        import re
        match = re.search(r'name="csrf-token" content="([^"]+)"', resp.text)
        if match:
            return match.group(1)
        return None
    except:
        return None

def swiggy_check(number):
    try:
        # First get CSRF token
        csrf = get_swiggy_csrf()
        if not csrf:
            return False, "⚠️ Failed to fetch CSRF token"
        
        url = "https://www.swiggy.com/dapi/auth/signin-with-check"
        payload = {"mobile": number, "password": "", "_csrf": csrf}
        headers = {
            "Content-Type": "application/json",
            "platform": "dweb",
            "user-id": "0",
            "User-Agent": get_random_user_agent(),
            "Accept": "application/json",
            "Origin": "https://www.swiggy.com",
            "Referer": "https://www.swiggy.com/"
        }
        response = safe_request("POST", url, json=payload, headers=headers)
        if not response:
            return False, "⚠️ Request timeout. Try again."
        
        if response.status_code != 200:
            return False, f"⚠️ API returned {response.status_code}"
        
        data = response.json()
        # statusCode 2 means success, but we need to check registration
        if data.get("statusCode") in (0, 2):
            registered = data.get("data", {}).get("registered", False)
            if registered:
                return True, "✅ Registered on Swiggy"
            else:
                return False, "❌ Not Registered on Swiggy"
        else:
            return False, f"⚠️ API Error: {data.get('statusMessage', 'Unknown')}"
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
        f"📝 <b>Example:</b> <code>9876543210</code>",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

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
    
    # Deduct points
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
