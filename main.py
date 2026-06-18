# main.py – Add these handlers after other callback handlers

# ==================== PREMIUM BUY HANDLER ====================
@bot.callback_query_handler(func=lambda call: call.data == "premium:buy")
@check_ban_callback
@require_join_callback
def premium_buy_handler(call):
    """Handle premium buy button – calls existing buy_premium from premium.py"""
    from premium import buy_premium
    buy_premium(call)

# ==================== BACK BUTTON HANDLER ====================
@bot.callback_query_handler(func=lambda call: call.data == "menu:back")
@check_ban_callback
@require_join_callback
def back_button_handler(call):
    """Handle back button – pop from navigation history"""
    user_id = call.from_user.id
    prev_menu = pop_nav(user_id)
    
    if not prev_menu or prev_menu == "menu:services":
        services_panel_handler(call.message)
    elif prev_menu.startswith("profile:"):
        profile_handler(call.message)
    elif prev_menu.startswith("support:"):
        support_handler(call.message)
    elif prev_menu.startswith("orders:"):
        orders_handler(call.message)
    elif prev_menu.startswith("track:"):
        track_handler(call.message)
    elif prev_menu.startswith("premium:"):
        premium_handler(call.message)
    elif prev_menu.startswith("refer:"):
        refer_handler(call.message)
    elif prev_menu.startswith("settings:"):
        next_page_handler(call.message)
    else:
        services_panel_handler(call.message)
    
    bot.answer_callback_query(call.id)
