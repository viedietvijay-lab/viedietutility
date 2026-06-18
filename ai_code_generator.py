# ai_code_generator.py
"""
AI Code Generator & Fixer – Powered by DeepSeek
"""

import telebot
import requests
import json
import re
from telebot import types
from bot_instance import bot
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, TOOL_COST
from database import Database
from points_manager import PointsManager
from buttons import create_colored_keyboard, back_button, main_menu

db = Database()
pm = PointsManager()

user_code_state = {}

# ==================== DEEPSEEK API ====================

def call_deepseek_api(prompt, system_prompt=None):
    """
    Call DeepSeek API for code generation or fixing
    """
    try:
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            print(f"DeepSeek API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"DeepSeek API Exception: {e}")
        return None

# ==================== AI TOOLS MENU ====================

@bot.callback_query_handler(func=lambda call: call.data == "menu:ai_tools")
def ai_tools_menu(call):
    """Show AI Tools menu"""
    user_id = call.from_user.id
    push_nav(user_id, "menu:ai_tools")
    
    buttons = [
        [("💻 Code Generator", "ai:code_gen", "primary")],
        [("🔧 Code Fixer", "ai:code_fixer", "success")],
        [("◀️ Back to Services", "menu:services", "primary")]
    ]
    
    bot.edit_message_text(
        "🤖 <b>AI TOOLS</b>\n\n"
        "Select a tool:\n\n"
        "💻 <b>Code Generator</b> – Generate code from description\n"
        "🔧 <b>Code Fixer</b> – Fix and debug your code\n\n"
        "⚡ Powered by DeepSeek AI",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=create_colored_keyboard(buttons)
    )
    bot.answer_callback_query(call.id)

# ==================== CODE GENERATOR ====================

@bot.callback_query_handler(func=lambda call: call.data == "ai:code_gen")
def code_gen_start(call):
    """Start code generation flow"""
    user_id = call.from_user.id
    
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return
    
    user_code_state[user_id] = {"step": "language", "mode": "generate"}
    
    buttons = [
        [("🐍 Python", "code_lang:python")],
        [("🌐 JavaScript", "code_lang:javascript")],
        [("☕ Java", "code_lang:java")],
        [("📦 C++", "code_lang:cpp")],
        [("🦀 Rust", "code_lang:rust")],
        [("📜 Go", "code_lang:go")],
        [("🔙 Back", "menu:ai_tools")]
    ]
    
    bot.edit_message_text(
        "💻 <b>AI Code Generator</b>\n\n"
        "Step 1: Select programming language:\n\n"
        "⚡ Powered by DeepSeek AI",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=create_colored_keyboard(buttons)
    )
    bot.answer_callback_query(call.id)

# ==================== CODE FIXER ====================

@bot.callback_query_handler(func=lambda call: call.data == "ai:code_fixer")
def code_fixer_start(call):
    """Start code fixer flow"""
    user_id = call.from_user.id
    
    if not pm.can_use_tool(user_id):
        bot.answer_callback_query(call.id, f"❌ Need {TOOL_COST} point!", show_alert=True)
        return
    
    user_code_state[user_id] = {"step": "code_input", "mode": "fix"}
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("◀️ Back", callback_data="menu:ai_tools", style="danger"))
    
    bot.edit_message_text(
        "🔧 <b>AI Code Fixer</b>\n\n"
        "Send me your code and describe the issue.\n\n"
        "📝 <b>Format:</b>\n"
        "1. Send the code\n"
        "2. Then send: <code>Error: your error message</code>\n\n"
        "Or send everything together:\n"
        "<pre>Your code here\n\nError: your error message</pre>\n\n"
        "⚡ Powered by DeepSeek AI",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

# ==================== LANGUAGE SELECTION ====================

@bot.callback_query_handler(func=lambda call: call.data.startswith("code_lang:"))
def code_language_selected(call):
    """Handle language selection for code generation"""
    user_id = call.from_user.id
    language = call.data.split(":")[1]
    
    lang_names = {
        "python": "Python 🐍",
        "javascript": "JavaScript 🌐",
        "java": "Java ☕",
        "cpp": "C++ 📦",
        "rust": "Rust 🦀",
        "go": "Go 📜"
    }
    lang_name = lang_names.get(language, language)
    
    user_code_state[user_id] = {
        "step": "prompt",
        "mode": "generate",
        "language": language,
        "language_name": lang_name
    }
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("◀️ Back", callback_data="menu:ai_tools", style="danger"))
    
    bot.edit_message_text(
        f"💻 <b>AI Code Generator</b>\n\n"
        f"Language: <b>{lang_name}</b>\n\n"
        f"Step 2: Describe what code you want.\n\n"
        f"📝 <b>Examples:</b>\n"
        f"• Write a function to sort a list\n"
        f"• Create a calculator app\n"
        f"• Fibonacci series in {language.title()}\n\n"
        f"Send your description:",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode='HTML',
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)

# ==================== CODE FIXER INPUT ====================

@bot.message_handler(func=lambda m: m.from_user.id in user_code_state and user_code_state[m.from_user.id].get("step") == "code_input")
def handle_code_fixer_input(message):
    """Handle code fixer input"""
    user_id = message.from_user.id
    text = message.text.strip()
    
    if not text:
        bot.send_message(user_id, "❌ Please send your code.")
        return
    
    # Deduct points
    if not pm.use_tool(user_id):
        bot.send_message(user_id, f"❌ Insufficient points! Need {TOOL_COST} point.", reply_markup=main_menu())
        del user_code_state[user_id]
        return
    
    # Show processing
    processing = bot.send_message(
        user_id,
        "🔧 <b>Analyzing and fixing code...</b>\n\nPlease wait a moment.\n\n⚡ Powered by DeepSeek AI",
        parse_mode='HTML'
    )
    
    # Build prompt for DeepSeek
    prompt = f"""Fix the following code. Identify all errors and provide the corrected code.

CODE:
