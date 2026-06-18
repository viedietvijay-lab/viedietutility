# buttons.py
from telebot import types

def create_colored_keyboard(buttons, row_width=1):
    """
    Creates an inline keyboard with color emojis in button text.
    buttons: list of lists, each inner list contains [text, callback_data]
    row_width: number of buttons per row
    """
    kb = types.InlineKeyboardMarkup(row_width=row_width)
    for row in buttons:
        btns = []
        for btn in row:
            text = btn[0]        # already includes emoji like 🔵, 🟢, 🔴
            callback = btn[1]
            btns.append(types.InlineKeyboardButton(text, callback_data=callback))
        kb.row(*btns)
    return kb

def main_menu():
    buttons = [
        [("🔵 Number Checker", "menu:num_checker")],
        [("🟢 Bypass Tools", "menu:bypass")],
        [("🔵 Downloaders", "menu:downloaders")],
        [("🟡 Firebase", "menu:firebase")],
        [("🟢 Image Tools", "menu:image")],
        [("🔵 UPI QR", "menu:upi")],
        [("🟡 Temp Mail", "menu:temp_mail")],
        [("🔴 Hash Tools", "menu:hash")],
        [("🔵 Profile", "menu:profile")],
        [("🟡 Support", "menu:support")],
        [("🟢 Premium", "menu:premium")]
    ]
    return create_colored_keyboard(buttons, row_width=2)

def back_button():
    return create_colored_keyboard([[("◀️ Back", "menu:main")]])