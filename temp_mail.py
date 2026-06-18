# temp_mail.py
import telebot
import requests, time, random, string, re, threading
from datetime import datetime, timedelta
from config import BOT_TOKEN, TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import back_button, main_menu, create_colored_keyboard

from bot_instance import bot
db = Database()
pm = PointsManager()

class TempMailBot:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.email = self.password = self.token = self.account_id = None
        self.messages = []
        self.is_waiting = False
        self.expiry_time = None

    def generate_email(self):
        try:
            domains = requests.get(f"{self.base_url}/domains", timeout=10).json().get('hydra:member', [])
            if not domains: return {'success': False, 'error': 'No domains'}
            domain = domains[0]['domain']
            username = 'user_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            address = f"{username}@{domain}"
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            acc = requests.post(f"{self.base_url}/accounts", json={'address': address, 'password': password},
                                headers={'Content-Type': 'application/json'}).json()
            token = requests.post(f"{self.base_url}/token", json={'address': address, 'password': password},
                                  headers={'Content-Type': 'application/json'}).json().get('token')
            self.email, self.password, self.token, self.account_id = address, password, token, acc.get('id')
            self.messages = []
            self.expiry_time = datetime.now() + timedelta(minutes=10)
            return {'success': True, 'email': address}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def check_inbox(self):
        if not self.token: return []
        try:
            r = requests.get(f"{self.base_url}/messages", headers={'Authorization': f'Bearer {self.token}'})
            if r.status_code == 200:
                msgs = r.json().get('hydra:member', [])
                for m in msgs:
                    if m not in self.messages: self.messages.append(m)
                return msgs
        except: pass
        return []

    def get_message_content(self, msg_id):
        try:
            r = requests.get(f"{self.base_url}/messages/{msg_id}", headers={'Authorization': f'Bearer {self.token}'})
            return r.json() if r.status_code == 200 else None
        except: return None

    def wait_for_otp(self, callback, timeout=120):
        self.is_waiting = True
        checked = set()
        for m in self.check_inbox(): checked.add(m['id'])
        start = time.time()
        while self.is_waiting and (time.time() - start) < timeout:
            msgs = self.check_inbox()
            for m in msgs:
                if m['id'] not in checked:
                    checked.add(m['id'])
                    full = self.get_message_content(m['id'])
                    if full:
                        body = full.get('text','') + full.get('html','')
                        subject = full.get('subject','')
                        combined = body + " " + subject
                        otp_match = re.search(r'\b\d{4,6}\b', combined)
                        if otp_match:
                            self.is_waiting = False
                            callback({
                                'otp': otp_match.group(),
                                'from': full.get('from',{}).get('address','Unknown'),
                                'from_name': full.get('from',{}).get('name',''),
                                'subject': subject,
                                'body': body[:500],
                                'time': datetime.now().strftime('%H:%M:%S')
                            })
                            return
            time.sleep(2)
        self.is_waiting = False
        callback(None)

temp_sessions = {}

@bot.callback_query_handler(func=lambda call: call.data == "menu:temp_mail")
def temp_mail_menu(call):
    buttons = [
        [("📧 New Email", "temp:new", "primary")],
        [("📥 Check Inbox", "temp:inbox", "success")],
        [("🔑 Get OTP", "temp:otp", "warning")],
        [("🗑️ Delete Email", "temp:delete", "danger")],
        [("◀️ Back", "menu:main", "primary")]
    ]
    bot.edit_message_text("📧 <b>Temp Mail</b>\n\nSelect option:",
                          chat_id=call.message.chat.id, message_id=call.message.message_id,
                          reply_markup=create_colored_keyboard(buttons))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("temp:"))
def temp_actions(call):
    user_id = call.from_user.id
    action = call.data.split(":")[1]
    if action == "new":
        if not pm.can_use_tool(user_id):
            bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
            return
        temp = TempMailBot()
        res = temp.generate_email()
        if res['success']:
            temp_sessions[user_id] = temp
            pm.use_tool(user_id)
            bot.send_message(user_id, f"📧 <b>New Email Created!</b>\n\n📧 <code>{res['email']}</code>\n⏱️ Expires: 10 min\n\nUse <b>Get OTP</b> to receive OTP")
        else:
            bot.send_message(user_id, f"❌ Failed: {res.get('error')}")
        bot.answer_callback_query(call.id)
        return

    if action == "inbox":
        temp = temp_sessions.get(user_id)
        if not temp:
            bot.answer_callback_query(call.id, "No email! Create one first.", show_alert=True)
            return
        msgs = temp.check_inbox()
        if not msgs:
            bot.send_message(user_id, "📭 No messages.")
        else:
            text = "📥 <b>Inbox</b>\n\n"
            for i, m in enumerate(msgs[-5:], 1):
                text += f"{i}. From: {m.get('from',{}).get('address','Unknown')}\n   Subject: {m.get('subject','No Subject')}\n\n"
            bot.send_message(user_id, text)
        bot.answer_callback_query(call.id)
        return

    if action == "otp":
        temp = temp_sessions.get(user_id)
        if not temp:
            bot.answer_callback_query(call.id, "No email! Create one first.", show_alert=True)
            return
        wait_msg = bot.send_message(user_id, "⏳ Waiting for OTP...")
        def cb(result):
            if result:
                bot.edit_message_text(f"🔑 <b>OTP Received!</b>\n\nOTP: <code>{result['otp']}</code>\nFrom: {result['from']}\nSubject: {result['subject']}",
                                      chat_id=user_id, message_id=wait_msg.message_id)
            else:
                bot.edit_message_text("❌ No OTP found in 2 minutes.", chat_id=user_id, message_id=wait_msg.message_id)
        threading.Thread(target=temp.wait_for_otp, args=(cb, 120), daemon=True).start()
        bot.answer_callback_query(call.id)
        return

    if action == "delete":
        temp_sessions.pop(user_id, None)
        bot.send_message(user_id, "🗑️ Email deleted.")
        bot.answer_callback_query(call.id)
        return
