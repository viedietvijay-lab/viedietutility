# config.py
import os

BOT_TOKEN = "7961583521:AAGVngUCauQqAO2S0Lt5G-8TCD6ldzN89WU"
ADMIN_IDS = [8139558808]

FORCE_CHANNEL = "@viedietlooters"
FORCE_GROUP = "https://t.me/viedietlooterschat"

# Points System
REFERRAL_POINTS = 8
TOOL_COST = 1
SIGNUP_BONUS = 5
PREMIUM_PRICE = 1  # ₹2

DB_PATH = "viediet_bot.db"

# Payment Gateway (replace with your actual API URL)
PAYMENT_API_URL = "https://api.yourgateway.com/create-order"
PAYMENT_SECRET_KEY = "PAY735DE219C41F68FBD1172102"

# 🔴 UPI ID for receiving payments
UPI_ID = "paytm.s1dw5n0@pty"

INDIA_COORDINATES = [
    {"lat": 28.6139, "lng": 77.2090},
    {"lat": 19.0760, "lng": 72.8777},
    {"lat": 13.0827, "lng": 80.2707},
    {"lat": 22.7196, "lng": 75.8577},
    {"lat": 26.8467, "lng": 80.9462},
    {"lat": 12.9716, "lng": 77.5946},
    {"lat": 17.3850, "lng": 78.4867},
    {"lat": 23.2599, "lng": 77.4126},
    {"lat": 21.1702, "lng": 72.8311},
    {"lat": 30.7333, "lng": 76.7794},
]

# ==================== DEEPSEEK AI API CONFIGURATION ====================
# 🔴 Yahan apni DeepSeek API key daalein
# Sign up at: https://platform.deepseek.com
DEEPSEEK_API_KEY = "sk-d6ec99e3e65d42779bd0a1a5d84836d6"   # <-- Replace with your actual key
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
