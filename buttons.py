# buttons.py
from telebot import types

# ==================== COLORED INLINE KEYBOARD ====================

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

# ==================== MAIN MENU (Backward Compat) ====================

def main_menu():
    return services_panel()

def back_button():
    return create_colored_keyboard([[("◀️ Back", "menu:back", "primary")]])

def services_back_button():
    return create_colored_keyboard([[("◀️ Back to Services", "menu:services", "primary")]])

# ==================== BOTTOM MENU (Reply Keyboard) ====================

def bottom_menu():
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [
        ["🛠️ Services", "👤 Profile", "📦 My Orders"],
        ["📦 Track Order", "⭐ Premium", "🔗 Refer"],
        ["🆘 Support", "📋 Next Page"]
    ]
    for row in buttons:
        keyboard.row(*row)
    return keyboard

# ==================== SERVICES PANEL (Colored) ====================

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
        [("⭐ Premium", "profile:premium", "warning")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== SUPPORT MENU ====================

def support_menu():
    buttons = [
        [("📞 Contact Admin", "support:contact", "primary")],
        [("🐛 Report Bug", "support:bug", "danger")],
        [("❓ FAQ", "support:faq", "success")],
        [("📖 User Guide", "support:guide", "warning")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== ORDERS MENU ====================

def orders_menu():
    buttons = [
        [("📋 Recent Orders", "orders:recent", "primary")],
        [("📊 Order History", "orders:history", "success")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== TRACK ORDER MENU ====================

def track_menu():
    buttons = [
        [("🔍 Track Order", "track:order", "primary")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== PREMIUM MENU ====================

def premium_menu():
    buttons = [
        [("💳 Buy Premium (₹49)", "premium:buy", "success")],
        [("⭐ Check Status", "premium:status", "primary")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== REFER MENU ====================

def refer_menu():
    buttons = [
        [("🔗 Get Referral Link", "refer:link", "success")],
        [("📊 Referral Stats", "refer:stats", "primary")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== NEXT PAGE MENU ====================

def next_page_menu():
    buttons = [
        [("⚙️ Settings", "settings:page", "primary")],
        [("🔐 Security", "security:page", "danger")],
        [("💡 Help Center", "help:page", "success")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)
