# buttons.py
from telebot import types

def create_colored_keyboard(buttons, row_width=1):
    kb = types.InlineKeyboardMarkup(row_width=row_width)
    for row in buttons:
        btns = []
        for btn in row:
            text = btn[0]
            callback = btn[1]
            style = btn[2] if len(btn) > 2 else None
            if style:
                btns.append(types.InlineKeyboardButton(text, callback_data=callback, style=style))
            else:
                btns.append(types.InlineKeyboardButton(text, callback_data=callback))
        kb.row(*btns)
    return kb

def main_menu():
    return services_panel()

def back_button():
    return create_colored_keyboard([[("◀️ Back", "menu:back", "danger")]])

# ==================== BOTTOM MENU ====================
def bottom_menu():
    """Only required buttons: Services, Profile, Refer, Support, Premium"""
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        ["🛠️ Services", "👤 Profile"],
        ["🔗 Refer", "🆘 Support"],
        ["⭐ Premium"]
    ]
    for row in buttons:
        keyboard.row(*row)
    return keyboard

# ==================== SERVICES PANEL ====================
def services_panel():
    buttons = [
        [("🤖 AI Tools", "menu:ai_tools", "primary")],
        [("📥 Downloaders", "menu:downloaders", "success")],
        [("🖼️ Image Tools", "menu:image_tools", "primary")],
        [("📄 PDF Tools", "menu:pdf_tools", "warning")],
        [("🌐 Web Tools", "menu:web_tools", "primary")],
        [("🔐 Hash Tools", "menu:hash_tools", "danger")],
        [("💰 Finance Tools", "menu:finance_tools", "success")],
        [("🔢 Number Checker", "menu:num_checker", "primary")],
        [("🔓 Bypass Tools", "menu:bypass", "warning")],
        [("📧 Temp Mail", "menu:temp_mail", "primary")],
        [("💳 UPI QR", "menu:upi", "success")],
        [("🖼️ Image to PDF", "menu:image", "primary")],
        [("🔥 Firebase", "menu:firebase", "warning")],
    ]
    return create_colored_keyboard(buttons, row_width=2)

# ==================== PROFILE MENU ====================
def profile_menu():
    buttons = [
        [("👤 My Account", "profile:account", "primary")],
        [("📊 My Stats", "profile:stats", "success")],
        [("◀️ Back", "menu:back", "danger")]
    ]
    return create_colored_keyboard(buttons)

# ==================== SUPPORT MENU ====================
def support_menu():
    buttons = [
        [("📞 Contact Admin", "support:contact", "primary")],
        [("🐛 Report Bug", "support:bug", "danger")],
        [("❓ FAQ", "support:faq", "success")],
        [("◀️ Back", "menu:back", "danger")]
    ]
    return create_colored_keyboard(buttons)

# ==================== REFER MENU ====================
def refer_menu():
    buttons = [
        [("🔗 Get Referral Link", "refer:link", "success")],
        [("📊 Referral Stats", "refer:stats", "primary")],
        [("◀️ Back", "menu:back", "danger")]
    ]
    return create_colored_keyboard(buttons)

# ==================== PREMIUM MENU ====================
def premium_menu():
    buttons = [
        [("💳 Buy Premium", "premium:buy", "success")],
        [("⭐ Check Status", "premium:status", "primary")],
        [("◀️ Back", "menu:back", "danger")]
    ]
    return create_colored_keyboard(buttons)
