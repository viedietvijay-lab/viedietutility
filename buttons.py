# buttons.py
from telebot import types

# ==================== COLORED INLINE KEYBOARD ====================

def create_colored_keyboard(buttons, row_width=1):
    """
    Creates an inline keyboard with colored buttons.
    buttons: list of lists, each inner list contains [text, callback_data, style]
    style: "primary", "success", "danger", "warning"
    """
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

# ==================== MAIN MENU (Compatibility) ====================

def main_menu():
    """
    Legacy main menu – now redirects to services panel.
    Kept for backward compatibility.
    """
    return services_panel()

# ==================== BACK BUTTONS ====================

def back_button():
    return create_colored_keyboard([[("◀️ Back", "menu:back", "primary")]])

def services_back_button():
    return create_colored_keyboard([[("◀️ Back to Services", "menu:services", "primary")]])

# ==================== BOTTOM MENU (Reply Keyboard) ====================

def bottom_menu():
    """
    Persistent bottom menu as Reply Keyboard.
    """
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [
        ["🛠️ Services", "👤 Profile", "📦 My Orders"],
        ["📦 Track Order", "💰 Deposit", "🔗 Refer"],
        ["🆘 Support", "📋 Next Page"]
    ]
    for row in buttons:
        keyboard.row(*row)
    return keyboard

# ==================== SERVICES PANEL (Colored Inline) ====================

def services_panel():
    """
    Services panel with colored category buttons.
    """
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

# ==================== MY ORDERS MENU ====================

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

# ==================== DEPOSIT MENU ====================

def deposit_menu():
    buttons = [
        [("💰 Deposit", "deposit:start", "success")],
        [("📊 Transaction History", "deposit:history", "primary")],
        [("◀️ Back", "menu:services", "primary")]
    ]
    return create_colored_keyboard(buttons)

# ==================== REFER MENU ====================

def refer_menu():
    buttons = [
        [("🔗 Refer Link", "refer:link", "success")],
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
