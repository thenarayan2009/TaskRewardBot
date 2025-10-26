#!/usr/bin/env python3
import telebot
from telebot import types
import threading
import time
import requests
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Flask

BOT_TOKEN = "8262209791:AAG6Tpczt77ajbdPVnTrpCOyUOEOD0AHJHU"
ADMIN_ID = 5367009004

BOT_USERNAME = os.getenv("BOT_USERNAME", "Tasktoearnmoneybot")
MINIMUM_WITHDRAWAL = 10
REFERRAL_REWARD = 2
REFERRAL_MILESTONE_COUNT = 5
REFERRAL_MILESTONE_REWARD = 10
DEFAULT_WELCOME_BONUS = 5
USERS_DATA_FILE = "data/users_data.json"
BOT_DATA_FILE = "data/bot_data.json"
BLOCKED_USERS_FILE = "data/blocked_users.json"
ACTIVITY_LOG_FILE = "data/activity_log.json"
TASK_SUBMISSIONS_FILE = "data/task_submissions.json"

admin_state = {}

MESSAGES = {
    "hindi": {
        "welcome": """🎉 स्वागत है! Task Reward Bot में आपका स्वागत है!

💰 कार्य पूरे करें और पैसे कमाएं
📸 स्क्रीनशॉट भेजकर कार्य सत्यापित करें
💵 न्यूनतम निकासी: ₹{min_withdrawal}
🔗 रेफर करें और ₹{referral_reward} प्रति रेफरल पाएं
🎁 वेलकम बोनस: ₹{welcome_bonus}

नीचे दिए गए बटन का उपयोग करें:""",
        "help": """📚 सहायता

🎯 नया कार्य: नए कार्य देखें
💰 बैलेंस: अपना बैलेंस चेक करें
💸 निकासी: पैसे निकालें (न्यूनतम ₹{min_withdrawal})
🔗 रेफर: दोस्तों को रेफर करें
❓ सहायता: यह मेसेज

⚠️ महत्वपूर्ण नियम:
• वास्तविक स्क्रीनशॉट भेजें
• नकली स्क्रीनशॉट से बैन हो सकते हैं
• एक कार्य केवल एक बार कर सकते हैं

📞 सहायता के लिए एडमिन से संपर्क करें""",
        "btn_new_task": "🎯 नया कार्य",
        "btn_balance": "💰 बैलेंस",
        "btn_withdrawal": "💸 निकासी",
        "btn_refer": "🔗 रेफर",
        "btn_help": "❓ सहायता",
        "btn_language": "🌐 भाषा",
        "no_tasks": "❌ कोई कार्य उपलब्ध नहीं\n⏳ नए कार्य के लिए बाद में आएं",
        "task_already_active": "⚠️ आपका कार्य पहले से चालू है\n📸 स्क्रीनशॉट भेजें या /newtask दबाएं",
        "task_assigned": "✅ कार्य सौंपा गया!\n\n📋 कार्य: {title}\n📝 विवरण: {description}\n🌐 लिंक: {link}\n💰 रिवार्ड: ₹{reward}\n\n📸 कार्य पूरा करने के बाद स्क्रीनशॉट भेजें",
        "balance_info": "💰 आपका बैलेंस\n\n💵 उपलब्ध बैलेंस: ₹{balance}\n📊 कुल कमाई: ₹{total_earnings}\n🎯 पूर्ण कार्य: {completed_tasks}\n🔗 रेफरल्स: {referrals}",
        "insufficient_balance": "❌ अपर्याप्त बैलेंस\n💰 आपका बैलेंस: ₹{balance}\n💸 न्यूनतम निकासी: ₹{min_withdrawal}",
        "enter_upi": "💳 कृपया अपना UPI ID भेजें\nउदाहरण: 9876543210@paytm",
        "withdrawal_submitted": "✅ निकासी अनुरोध भेजा गया\n⏳ एडमिन द्वारा सत्यापन की प्रतीक्षा करें\n💰 राशि: ₹{amount}\n🏦 UPI: {upi_id}",
        "referral_info": """🔗 आपका रेफरल लिंक

{referral_link}

📊 आंकड़े:
🔗 कुल रेफरल्स: {referrals_count}
💰 रेफरल कमाई: ₹{referral_earnings}

🎁 रेफरल रिवार्ड:
• प्रत्येक रेफरल: ₹{referral_reward}
• {milestone_count} रेफरल पर बोनस: ₹{milestone_reward}

💡 अपने दोस्तों के साथ लिंक शेयर करें!""",
        "no_active_task": "❌ कोई सक्रिय कार्य नहीं\n🎯 पहले /newtask दबाएं",
        "screenshot_submitted": "✅ स्क्रीनशॉट भेजा गया\n⏳ सत्यापन के लिए प्रतीक्षा करें\n📝 एडमिन जल्द ही आपके कार्य की जांच करेंगे",
        "user_blocked": "🚫 आप इस बॉट का उपयोग नहीं कर सकते",
        "start_first": "❌ कृपया पहले /start दबाएं",
        "invalid_format": "❌ गलत फॉर्मेट। सही फॉर्मेट का उपयोग करें।",
        "select_language": "🌐 भाषा चुनें\nSelect Language:",
        "language_changed": "✅ भाषा बदली गई!",
        "menu_text": "📋 मेनू के लिए /start दबाएं या नीचे दिए गए बटन का उपयोग करें",
        "welcome_bonus_received": "🎁 वेलकम बोनस!\n\n💰 आपको ₹{amount} का वेलकम बोनस मिला है!",
        "task_approved": "✅ कार्य स्वीकृत!\n\n📋 कार्य: {title}\n💰 रिवार्ड: ₹{reward}\n💵 नया बैलेंस: ₹{balance}",
        "task_rejected": "❌ कार्य अस्वीकृत\n\n📋 कार्य: {title}\n📝 कारण: {reason}\n\n🔄 कृपया पुनः प्रयास करें",
        "task_limit_reached": "⚠️ यह कार्य पूरा हो गया है\n📊 कार्य पूर्ण: {assigned}/{quantity}\n\n🎯 अन्य कार्य देखें: /newtask"
    },
    "english": {
        "welcome": """🎉 Welcome to Task Reward Bot!

💰 Complete tasks and earn money
📸 Submit screenshots to verify tasks
💵 Minimum withdrawal: ₹{min_withdrawal}
🔗 Refer friends and earn ₹{referral_reward} per referral
🎁 Welcome Bonus: ₹{welcome_bonus}

Use the buttons below:""",
        "help": """📚 Help

🎯 New Task: View available tasks
💰 Balance: Check your balance
💸 Withdrawal: Withdraw money (minimum ₹{min_withdrawal})
🔗 Refer: Refer friends
❓ Help: This message

⚠️ Important Rules:
• Submit real screenshots
• Fake screenshots will result in ban
• Each task can only be completed once

📞 Contact admin for support""",
        "btn_new_task": "🎯 New Task",
        "btn_balance": "💰 Balance",
        "btn_withdrawal": "💸 Withdrawal",
        "btn_refer": "🔗 Refer",
        "btn_help": "❓ Help",
        "btn_language": "🌐 Language",
        "no_tasks": "❌ No tasks available\n⏳ Check back later for new tasks",
        "task_already_active": "⚠️ You already have an active task\n📸 Submit screenshot or press /newtask",
        "task_assigned": "✅ Task assigned!\n\n📋 Task: {title}\n📝 Description: {description}\n🌐 Link: {link}\n💰 Reward: ₹{reward}\n\n📸 Submit screenshot after completing the task",
        "balance_info": "💰 Your Balance\n\n💵 Available Balance: ₹{balance}\n📊 Total Earnings: ₹{total_earnings}\n🎯 Completed Tasks: {completed_tasks}\n🔗 Referrals: {referrals}",
        "insufficient_balance": "❌ Insufficient balance\n💰 Your balance: ₹{balance}\n💸 Minimum withdrawal: ₹{min_withdrawal}",
        "enter_upi": "💳 Please send your UPI ID\nExample: 9876543210@paytm",
        "withdrawal_submitted": "✅ Withdrawal request submitted\n⏳ Wait for admin verification\n💰 Amount: ₹{amount}\n🏦 UPI: {upi_id}",
        "referral_info": """🔗 Your Referral Link

{referral_link}

📊 Statistics:
🔗 Total Referrals: {referrals_count}
💰 Referral Earnings: ₹{referral_earnings}

🎁 Referral Rewards:
• Each referral: ₹{referral_reward}
• Bonus at {milestone_count} referrals: ₹{milestone_reward}

💡 Share the link with your friends!""",
        "no_active_task": "❌ No active task\n🎯 Press /newtask first",
        "screenshot_submitted": "✅ Screenshot submitted\n⏳ Waiting for verification\n📝 Admin will verify your task soon",
        "user_blocked": "🚫 You are blocked from using this bot",
        "start_first": "❌ Please press /start first",
        "invalid_format": "❌ Invalid format. Please use correct format.",
        "select_language": "🌐 Select Language\nभाषा चुनें:",
        "language_changed": "✅ Language changed!",
        "menu_text": "📋 Press /start for menu or use the buttons below",
        "welcome_bonus_received": "🎁 Welcome Bonus!\n\n💰 You received ₹{amount} as welcome bonus!",
        "task_approved": "✅ Task Approved!\n\n📋 Task: {title}\n💰 Reward: ₹{reward}\n💵 New Balance: ₹{balance}",
        "task_rejected": "❌ Task Rejected\n\n📋 Task: {title}\n📝 Reason: {reason}\n\n🔄 Please try again",
        "task_limit_reached": "⚠️ This task is full\n📊 Task Completed: {assigned}/{quantity}\n\n🎯 Try other tasks: /newtask"
    }
}

def get_message(user_language, key, **kwargs):
    if user_language not in MESSAGES:
        user_language = "hindi"
    message = MESSAGES[user_language].get(key, MESSAGES["hindi"].get(key, "Message not found"))
    if kwargs:
        try:
            return message.format(**kwargs)
        except:
            return message
    return message

def get_language_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    hindi_btn = types.InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hindi")
    english_btn = types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_english")
    keyboard.add(hindi_btn, english_btn)
    return keyboard

def ensure_data_directory():
    if not os.path.exists("data"):
        os.makedirs("data")

def initialize_data_files():
    ensure_data_directory()
    if not os.path.exists(USERS_DATA_FILE):
        with open(USERS_DATA_FILE, 'w') as f:
            json.dump({}, f)
    if not os.path.exists(BOT_DATA_FILE):
        initial_data = {
            "tasks": [],
            "withdrawal_requests": [],
            "settings": {
                "min_withdrawal": MINIMUM_WITHDRAWAL,
                "referral_reward": REFERRAL_REWARD,
                "default_welcome_bonus": DEFAULT_WELCOME_BONUS,
                "referral_milestone_count": REFERRAL_MILESTONE_COUNT,
                "referral_milestone_reward": REFERRAL_MILESTONE_REWARD
            }
        }
        with open(BOT_DATA_FILE, 'w') as f:
            json.dump(initial_data, f, indent=2)
    if not os.path.exists(BLOCKED_USERS_FILE):
        with open(BLOCKED_USERS_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(ACTIVITY_LOG_FILE):
        with open(ACTIVITY_LOG_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(TASK_SUBMISSIONS_FILE):
        with open(TASK_SUBMISSIONS_FILE, 'w') as f:
            json.dump([], f)

def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {} if filepath in [USERS_DATA_FILE] else []

def save_json_file(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def get_all_users_data():
    return load_json_file(USERS_DATA_FILE)

def get_user_data(user_id):
    users_data = get_all_users_data()
    return users_data.get(str(user_id), {})

def user_exists(user_id):
    users_data = get_all_users_data()
    return str(user_id) in users_data

def create_user(user_id, first_name, username, referrer_id=None):
    users_data = get_all_users_data()
    bot_data = get_bot_data()
    settings = bot_data.get("settings", {})
    default_welcome_bonus = settings.get("default_welcome_bonus", DEFAULT_WELCOME_BONUS)
    
    user_data = {
        "id": user_id,
        "first_name": first_name,
        "username": username,
        "balance": 0,
        "total_earnings": 0,
        "completed_tasks": [],
        "referrals": 0,
        "referred_by": referrer_id,
        "joined_at": time.time(),
        "current_task": None,
        "language": "hindi",
        "custom_settings": {
            "referral_reward": None,
            "milestone_count": None,
            "milestone_reward": None,
            "welcome_bonus": default_welcome_bonus
        }
    }
    users_data[str(user_id)] = user_data
    save_json_file(USERS_DATA_FILE, users_data)

def get_user_custom_setting(user_id, setting_key, default_value):
    user_data = get_user_data(user_id)
    if user_data and "custom_settings" in user_data:
        custom_value = user_data["custom_settings"].get(setting_key)
        if custom_value is not None:
            return custom_value
    return default_value

def set_user_custom_setting(user_id, setting_key, value):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        if "custom_settings" not in users_data[str(user_id)]:
            users_data[str(user_id)]["custom_settings"] = {}
        users_data[str(user_id)]["custom_settings"][setting_key] = value
        save_json_file(USERS_DATA_FILE, users_data)
        return True
    return False

def add_user_balance(user_id, amount):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        users_data[str(user_id)]["balance"] = users_data[str(user_id)].get("balance", 0) + amount
        users_data[str(user_id)]["total_earnings"] = users_data[str(user_id)].get("total_earnings", 0) + amount
        save_json_file(USERS_DATA_FILE, users_data)

def deduct_user_balance(user_id, amount):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        current_balance = users_data[str(user_id)].get("balance", 0)
        new_balance = max(0, current_balance - amount)
        users_data[str(user_id)]["balance"] = new_balance
        save_json_file(USERS_DATA_FILE, users_data)

def add_completed_task(user_id, task_id):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        completed_tasks = users_data[str(user_id)].get("completed_tasks", [])
        if task_id not in completed_tasks:
            completed_tasks.append(task_id)
            users_data[str(user_id)]["completed_tasks"] = completed_tasks
            save_json_file(USERS_DATA_FILE, users_data)

def increment_user_referrals(user_id):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        users_data[str(user_id)]["referrals"] = users_data[str(user_id)].get("referrals", 0) + 1
        save_json_file(USERS_DATA_FILE, users_data)

def set_user_current_task(user_id, task_id):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        users_data[str(user_id)]["current_task"] = task_id
        save_json_file(USERS_DATA_FILE, users_data)

def clear_user_current_task(user_id):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        users_data[str(user_id)]["current_task"] = None
        save_json_file(USERS_DATA_FILE, users_data)

def get_bot_data():
    return load_json_file(BOT_DATA_FILE)

def save_bot_data(data):
    save_json_file(BOT_DATA_FILE, data)

def add_withdrawal_request(request):
    bot_data = get_bot_data()
    if "withdrawal_requests" not in bot_data:
        bot_data["withdrawal_requests"] = []
    bot_data["withdrawal_requests"].append(request)
    save_bot_data(bot_data)

def add_task(task):
    bot_data = get_bot_data()
    if "tasks" not in bot_data:
        bot_data["tasks"] = []
    bot_data["tasks"].append(task)
    save_bot_data(bot_data)

def get_blocked_users():
    return load_json_file(BLOCKED_USERS_FILE)

def is_user_blocked(user_id):
    blocked_users = get_blocked_users()
    return user_id in blocked_users

def block_user(user_id):
    blocked_users = get_blocked_users()
    if user_id not in blocked_users:
        blocked_users.append(user_id)
        save_json_file(BLOCKED_USERS_FILE, blocked_users)

def unblock_user(user_id):
    blocked_users = get_blocked_users()
    if user_id in blocked_users:
        blocked_users.remove(user_id)
        save_json_file(BLOCKED_USERS_FILE, blocked_users)

def update_withdrawal_request_status(request_id, status):
    bot_data = get_bot_data()
    withdrawal_requests = bot_data.get("withdrawal_requests", [])
    for request in withdrawal_requests:
        if request["id"] == request_id:
            request["status"] = status
            request["processed_at"] = time.time()
            break
    save_bot_data(bot_data)

def get_user_language(user_id):
    user_data = get_user_data(user_id)
    if user_data:
        return user_data.get("language", "hindi")
    return "hindi"

def set_user_language(user_id, language):
    users_data = get_all_users_data()
    if str(user_id) in users_data:
        users_data[str(user_id)]["language"] = language
        save_json_file(USERS_DATA_FILE, users_data)

def log_activity(user_id, action, data=None):
    try:
        try:
            with open(ACTIVITY_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
        log_entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "action": action,
            "data": data or {},
            "datetime": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        logs.append(log_entry)
        if len(logs) > 10000:
            logs = logs[-10000:]
        with open(ACTIVITY_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Logging error: {e}")
        return False

def broadcast_notification(message_text, exclude_user_id=None):
    """Send notification to all active users"""
    users_data = get_all_users_data()
    success_count = 0
    failed_count = 0
    
    for user_id_str, user_data in users_data.items():
        user_id = int(user_id_str)
        if exclude_user_id and user_id == exclude_user_id:
            continue
        if is_user_blocked(user_id):
            continue
        
        try:
            bot.send_message(user_id, message_text, parse_mode='Markdown')
            success_count += 1
            time.sleep(0.05)
        except Exception as e:
            failed_count += 1
            print(f"Broadcast failed for {user_id}: {e}")
    
    return success_count, failed_count

app = Flask(__name__)

@app.route('/')
def home():
    return """<!DOCTYPE html>
<html>
<head><title>Telegram Task Bot</title><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial,sans-serif;margin:0;padding:20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;text-align:center;min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center}.container{background:rgba(255,255,255,0.1);padding:40px;border-radius:20px;backdrop-filter:blur(10px);box-shadow:0 8px 32px rgba(0,0,0,0.1);max-width:500px}.status{font-size:24px;margin-bottom:20px}.emoji{font-size:64px;margin-bottom:20px}.info{font-size:16px;opacity:0.8;line-height:1.6}.pulse{animation:pulse 2s infinite}@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.05)}100%{transform:scale(1)}}</style>
</head>
<body><div class="container"><div class="emoji pulse">🤖</div><div class="status">Telegram Task Bot is Running!</div>
<div class="info"><p>✅ Bot Status: Online 24/7</p><p>🕐 Server Time: """ + time.strftime('%Y-%m-%d %H:%M:%S UTC') + """</p><p>🚀 Ready to serve users</p><p>🔄 Auto-restart enabled</p></div></div></body></html>"""

@app.route('/ping')
def ping():
    return "Bot is alive!"

@app.route('/health')
def health():
    return {"status": "UP", "service": "telegram-bot"}

@app.route('/alive')
def alive():
    return "UP"

@app.route('/status')
def status():
    return {"status": "online", "message": "🤖 Bot is alive!", "timestamp": time.strftime('%Y-%m-%d %H:%M:%S UTC'), "uptime": "24/7", "deployment": "stable"}

def run_server():
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ Keep-alive server error: {e}")

def keep_alive():
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    print("🌐 Keep-alive server started on port 5000")

bot = telebot.TeleBot(BOT_TOKEN)

initialize_data_files()

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        bot.reply_to(message, "🚫 आप इस बॉट का उपयोग नहीं कर सकते / You are blocked from using this bot")
        return
    
    is_new_user = False
    if not user_exists(user_id):
        is_new_user = True
        referrer_id = None
        if len(message.text.split()) > 1:
            try:
                referrer_id = int(message.text.split()[1])
                if user_exists(referrer_id) and referrer_id != user_id:
                    bot_data = get_bot_data()
                    settings = bot_data.get("settings", {})
                    
                    referrer_custom_reward = get_user_custom_setting(referrer_id, "referral_reward", None)
                    if referrer_custom_reward is not None:
                        referral_reward = referrer_custom_reward
                    else:
                        referral_reward = settings.get("referral_reward", REFERRAL_REWARD)
                    
                    referrer_custom_milestone_count = get_user_custom_setting(referrer_id, "milestone_count", None)
                    if referrer_custom_milestone_count is not None:
                        milestone_count = referrer_custom_milestone_count
                    else:
                        milestone_count = settings.get("referral_milestone_count", REFERRAL_MILESTONE_COUNT)
                    
                    referrer_custom_milestone_reward = get_user_custom_setting(referrer_id, "milestone_reward", None)
                    if referrer_custom_milestone_reward is not None:
                        milestone_reward = referrer_custom_milestone_reward
                    else:
                        milestone_reward = settings.get("referral_milestone_reward", REFERRAL_MILESTONE_REWARD)
                    
                    add_user_balance(referrer_id, referral_reward)
                    increment_user_referrals(referrer_id)
                    updated_referrer_data = get_user_data(referrer_id)
                    new_referral_count = updated_referrer_data['referrals']
                    
                    if new_referral_count % milestone_count == 0:
                        add_user_balance(referrer_id, milestone_reward)
                        bot.send_message(referrer_id, f"🎉 Milestone Bonus!\n\nआपने {milestone_count} referrals complete किए हैं!\nबोनस: ₹{milestone_reward}")
                    
                    bot.send_message(referrer_id, f"🎉 New Referral!\n\nआपके रेफरल से एक नया user join हुआ!\nरिवॉर्ड: ₹{referral_reward}\nकुल रेफरल्स: {new_referral_count}")
                    log_activity(referrer_id, "referral_earned", {"referred_user": user_id, "reward": referral_reward, "total_referrals": new_referral_count})
            except:
                referrer_id = None
        
        create_user(user_id, message.from_user.first_name, message.from_user.username, referrer_id)
        
        welcome_bonus = get_user_custom_setting(user_id, "welcome_bonus", DEFAULT_WELCOME_BONUS)
        if welcome_bonus > 0:
            add_user_balance(user_id, welcome_bonus)
            user_language = get_user_language(user_id)
            bot.send_message(user_id, get_message(user_language, "welcome_bonus_received", amount=welcome_bonus))
            log_activity(user_id, "welcome_bonus_received", {"amount": welcome_bonus})
        
        log_activity(user_id, "user_registered", {"referrer": referrer_id})
    
    user_language = get_user_language(user_id)
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    btn1 = types.KeyboardButton(get_message(user_language, "btn_new_task"))
    btn2 = types.KeyboardButton(get_message(user_language, "btn_balance"))
    btn3 = types.KeyboardButton(get_message(user_language, "btn_withdrawal"))
    btn4 = types.KeyboardButton(get_message(user_language, "btn_refer"))
    btn5 = types.KeyboardButton(get_message(user_language, "btn_help"))
    btn6 = types.KeyboardButton(get_message(user_language, "btn_language"))
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    keyboard.add(btn5, btn6)
    
    bot_data = get_bot_data()
    settings = bot_data.get("settings", {})
    min_withdrawal = settings.get("min_withdrawal", MINIMUM_WITHDRAWAL)
    referral_reward = settings.get("referral_reward", REFERRAL_REWARD)
    welcome_bonus = settings.get("default_welcome_bonus", DEFAULT_WELCOME_BONUS)
    
    welcome_msg = get_message(user_language, "welcome", min_withdrawal=min_withdrawal, referral_reward=referral_reward, welcome_bonus=welcome_bonus)
    bot.reply_to(message, welcome_msg, reply_markup=keyboard)
    log_activity(user_id, "start_command", {})

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("💸 Withdrawal Requests", callback_data="admin_withdrawals")
    btn2 = types.InlineKeyboardButton("🎯 Manage Tasks", callback_data="admin_tasks")
    btn3 = types.InlineKeyboardButton("📊 User Statistics", callback_data="admin_stats")
    btn4 = types.InlineKeyboardButton("💰 Adjust Balance", callback_data="admin_adjust_balance")
    btn5 = types.InlineKeyboardButton("🚫 Block/Unblock User", callback_data="admin_block_user")
    btn6 = types.InlineKeyboardButton("📨 Message Center", callback_data="admin_message_center")
    btn7 = types.InlineKeyboardButton("🔗 Referral Settings", callback_data="admin_referral_settings")
    btn8 = types.InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_global_settings")
    refresh_btn = types.InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
    
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn4)
    keyboard.add(btn5, btn6)
    keyboard.add(btn7, btn8)
    keyboard.add(refresh_btn)
    
    admin_msg = """🔧 **Admin Panel**

Select an option:

💸 Withdrawal Requests - Manage user withdrawals
🎯 Manage Tasks - Add/Edit tasks
📊 User Statistics - View all user stats
💰 Adjust Balance - Add/deduct user balance
🚫 Block/Unblock - Block or unblock users
📨 Message Center - Broadcast messages
🔗 Referral Settings - Per-user referral settings
⚙️ Bot Settings - Global bot settings
🔄 Refresh Panel - Refresh this panel"""
    
    bot.send_message(ADMIN_ID, admin_msg, reply_markup=keyboard, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
def handle_admin_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    
    if call.data == "admin_users_list":
        users_data = get_all_users_data()
        total_users = len(users_data)
        
        if total_users == 0:
            bot.edit_message_text("❌ कोई user नहीं है", call.message.chat.id, call.message.message_id)
            return
        
        page = 0
        users_per_page = 10
        show_users_page(call.message.chat.id, call.message.message_id, page, users_per_page)
    
    elif call.data == "admin_stats":
        show_users_page(call.message.chat.id, call.message.message_id, 0, 10)
    
    elif call.data == "admin_referral_settings":
        msg = bot.edit_message_text("🔍 User ID enter करें जिसके referral settings change करने हैं:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "search_user_for_referral", "message_id": msg.message_id}
    
    elif call.data == "admin_adjust_balance":
        msg = bot.edit_message_text("🔍 User ID enter करें जिसका balance adjust करना है:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "search_user_for_balance", "message_id": msg.message_id}
    
    elif call.data == "admin_block_user":
        msg = bot.edit_message_text("🔍 User ID enter करें जिसे block/unblock करना है:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "search_user_for_block", "message_id": msg.message_id}
    
    elif call.data == "admin_withdrawals":
        bot_data = get_bot_data()
        withdrawal_requests = bot_data.get("withdrawal_requests", [])
        pending = [w for w in withdrawal_requests if w.get("status") == "pending"]
        
        if not pending:
            keyboard = types.InlineKeyboardMarkup()
            back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
            keyboard.add(back_btn)
            bot.edit_message_text("✅ कोई pending withdrawal नहीं है", call.message.chat.id, call.message.message_id, reply_markup=keyboard)
            return
        
        msg = f"💸 **Pending Withdrawals** ({len(pending)})\n\n"
        for w in pending[:5]:
            msg += f"User: {w['user_id']}\nAmount: ₹{w['amount']}\nUPI: {w['upi_id']}\n\n"
        
        keyboard = types.InlineKeyboardMarkup()
        back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
        keyboard.add(back_btn)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data == "admin_tasks":
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        msg = f"🎯 **Task Management**\n\n📋 Total Tasks: {len(tasks)}\n\n"
        
        if tasks:
            active_tasks = [t for t in tasks if t.get("active", True)]
            inactive_tasks = [t for t in tasks if not t.get("active", True)]
            msg += f"✅ Active: {len(active_tasks)}\n❌ Inactive: {len(inactive_tasks)}\n\n"
            
            for i, task in enumerate(tasks[:5], 1):
                status = "✅" if task.get("active", True) else "❌"
                completed = task.get("completed_count", 0)
                quantity = task.get("quantity", 999999)
                msg += f"{i}. {status} {task['title']}\n   Reward: ₹{task['reward']} | Done: {completed}/{quantity}\n\n"
        else:
            msg += "⚠️ No tasks available\n\n"
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        add_btn = types.InlineKeyboardButton("➕ Add New Task", callback_data="admin_task_add")
        if tasks:
            view_btn = types.InlineKeyboardButton("📋 View All Tasks", callback_data="admin_task_view_0")
            keyboard.add(add_btn, view_btn)
        else:
            keyboard.add(add_btn)
        back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
        keyboard.add(back_btn)
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data == "admin_message_center":
        msg = """📨 **Message Center**

Choose message type:

👤 **Single User** - Send message to specific user
📢 **Broadcast** - Send message to all users"""
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("👤 Send to Single User", callback_data="admin_msg_single")
        btn2 = types.InlineKeyboardButton("📢 Broadcast to All Users", callback_data="admin_msg_broadcast")
        back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
        keyboard.add(btn1, btn2, back_btn)
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data == "admin_refresh":
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("💸 Withdrawal Requests", callback_data="admin_withdrawals")
        btn2 = types.InlineKeyboardButton("🎯 Manage Tasks", callback_data="admin_tasks")
        btn3 = types.InlineKeyboardButton("📊 User Statistics", callback_data="admin_stats")
        btn4 = types.InlineKeyboardButton("💰 Adjust Balance", callback_data="admin_adjust_balance")
        btn5 = types.InlineKeyboardButton("🚫 Block/Unblock User", callback_data="admin_block_user")
        btn6 = types.InlineKeyboardButton("📨 Message Center", callback_data="admin_message_center")
        btn7 = types.InlineKeyboardButton("🔗 Referral Settings", callback_data="admin_referral_settings")
        btn8 = types.InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_global_settings")
        refresh_btn = types.InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
        
        keyboard.add(btn1, btn2)
        keyboard.add(btn3, btn4)
        keyboard.add(btn5, btn6)
        keyboard.add(btn7, btn8)
        keyboard.add(refresh_btn)
        
        admin_msg = """🔧 **Admin Panel**

Select an option:

💸 Withdrawal Requests - Manage user withdrawals
🎯 Manage Tasks - Add/Edit tasks
📊 User Statistics - View all user stats
💰 Adjust Balance - Add/deduct user balance
🚫 Block/Unblock - Block or unblock users
📨 Message Center - Broadcast messages
🔗 Referral Settings - Per-user referral settings
⚙️ Bot Settings - Global bot settings
🔄 Refresh Panel - Refresh this panel"""
        
        bot.edit_message_text(admin_msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data == "admin_search_user":
        msg = bot.edit_message_text("🔍 User ID भेजें (number):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "search_user", "message_id": msg.message_id}
    
    elif call.data == "admin_global_settings":
        bot_data = get_bot_data()
        settings = bot_data.get("settings", {})
        
        msg = f"""⚙️ **Global Default Settings**

💸 Min Withdrawal: ₹{settings.get('min_withdrawal', MINIMUM_WITHDRAWAL)}
🔗 Referral Reward: ₹{settings.get('referral_reward', REFERRAL_REWARD)}
🎯 Milestone Count: {settings.get('referral_milestone_count', REFERRAL_MILESTONE_COUNT)}
🎁 Milestone Reward: ₹{settings.get('referral_milestone_reward', REFERRAL_MILESTONE_REWARD)}
🎉 Welcome Bonus: ₹{settings.get('default_welcome_bonus', DEFAULT_WELCOME_BONUS)}

ℹ️ These are default values for ALL users."""
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("💸 Edit Min Withdrawal", callback_data="admin_edit_global_min_withdrawal")
        btn2 = types.InlineKeyboardButton("🔗 Edit Referral Reward", callback_data="admin_edit_global_ref_reward")
        btn3 = types.InlineKeyboardButton("🎯 Edit Milestone Count", callback_data="admin_edit_global_milestone_count")
        btn4 = types.InlineKeyboardButton("🎁 Edit Milestone Reward", callback_data="admin_edit_global_milestone_reward")
        btn5 = types.InlineKeyboardButton("🎉 Edit Welcome Bonus", callback_data="admin_edit_global_welcome_bonus")
        back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_back")
        keyboard.add(btn1, btn2, btn3, btn4, btn5, back_btn)
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data == "admin_back":
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton("💸 Withdrawal Requests", callback_data="admin_withdrawals")
        btn2 = types.InlineKeyboardButton("🎯 Manage Tasks", callback_data="admin_tasks")
        btn3 = types.InlineKeyboardButton("📊 User Statistics", callback_data="admin_stats")
        btn4 = types.InlineKeyboardButton("💰 Adjust Balance", callback_data="admin_adjust_balance")
        btn5 = types.InlineKeyboardButton("🚫 Block/Unblock User", callback_data="admin_block_user")
        btn6 = types.InlineKeyboardButton("📨 Message Center", callback_data="admin_message_center")
        btn7 = types.InlineKeyboardButton("🔗 Referral Settings", callback_data="admin_referral_settings")
        btn8 = types.InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_global_settings")
        refresh_btn = types.InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
        
        keyboard.add(btn1, btn2)
        keyboard.add(btn3, btn4)
        keyboard.add(btn5, btn6)
        keyboard.add(btn7, btn8)
        keyboard.add(refresh_btn)
        
        admin_msg = """🔧 **Admin Panel**

Select an option:

💸 Withdrawal Requests - Manage user withdrawals
🎯 Manage Tasks - Add/Edit tasks
📊 User Statistics - View all user stats
💰 Adjust Balance - Add/deduct user balance
🚫 Block/Unblock - Block or unblock users
📨 Message Center - Broadcast messages
🔗 Referral Settings - Per-user referral settings
⚙️ Bot Settings - Global bot settings
🔄 Refresh Panel - Refresh this panel"""
        
        bot.edit_message_text(admin_msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data.startswith("admin_page_"):
        page = int(call.data.split("_")[-1])
        show_users_page(call.message.chat.id, call.message.message_id, page, 10)
    
    elif call.data.startswith("admin_view_user_"):
        user_id = int(call.data.replace("admin_view_user_", ""))
        show_user_details(call.message.chat.id, call.message.message_id, user_id)
    
    elif call.data.startswith("admin_edit_user_"):
        user_id = int(call.data.replace("admin_edit_user_", ""))
        show_user_edit_options(call.message.chat.id, call.message.message_id, user_id)
    
    elif call.data.startswith("admin_set_ref_reward_"):
        user_id = int(call.data.replace("admin_set_ref_reward_", ""))
        msg = bot.edit_message_text(f"💰 User {user_id} के लिए Referral Reward enter करें:\n\n(रुपये में, या 'default' type करें)", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "set_ref_reward", "user_id": user_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_set_milestone_count_"):
        user_id = int(call.data.replace("admin_set_milestone_count_", ""))
        msg = bot.edit_message_text(f"🎯 User {user_id} के लिए Milestone Count enter करें:\n\n(number, या 'default' type करें)", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "set_milestone_count", "user_id": user_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_set_milestone_reward_"):
        user_id = int(call.data.replace("admin_set_milestone_reward_", ""))
        msg = bot.edit_message_text(f"🎁 User {user_id} के लिए Milestone Reward enter करें:\n\n(रुपये में, या 'default' type करें)", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "set_milestone_reward", "user_id": user_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_set_welcome_bonus_"):
        user_id = int(call.data.replace("admin_set_welcome_bonus_", ""))
        msg = bot.edit_message_text(f"🎉 User {user_id} के लिए Welcome Bonus enter करें:\n\n(रुपये में, या 'default' type करें)", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "set_welcome_bonus", "user_id": user_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_add_balance_"):
        user_id = int(call.data.replace("admin_add_balance_", ""))
        msg = bot.edit_message_text(f"💰 User {user_id} के balance में add करने के लिए amount enter करें:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "add_balance", "user_id": user_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_deduct_balance_"):
        user_id = int(call.data.replace("admin_deduct_balance_", ""))
        msg = bot.edit_message_text(f"💸 User {user_id} के balance से deduct करने के लिए amount enter करें:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "deduct_balance", "user_id": user_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_block_"):
        user_id = int(call.data.replace("admin_block_", ""))
        block_user(user_id)
        bot.answer_callback_query(call.id, f"✅ User {user_id} blocked successfully!")
        bot.edit_message_text(f"🚫 User {user_id} has been blocked", call.message.chat.id, call.message.message_id)
        log_activity(ADMIN_ID, "user_blocked_by_admin", {"user_id": user_id})
        try:
            bot.send_message(user_id, "🚫 आपका account admin द्वारा block कर दिया गया है।")
        except:
            pass
    
    elif call.data.startswith("admin_unblock_"):
        user_id = int(call.data.replace("admin_unblock_", ""))
        unblock_user(user_id)
        bot.answer_callback_query(call.id, f"✅ User {user_id} unblocked successfully!")
        bot.edit_message_text(f"✅ User {user_id} has been unblocked", call.message.chat.id, call.message.message_id)
        log_activity(ADMIN_ID, "user_unblocked_by_admin", {"user_id": user_id})
        try:
            bot.send_message(user_id, "✅ आपका account unblock कर दिया गया है। अब आप bot use कर सकते हैं।")
        except:
            pass
    
    elif call.data == "admin_edit_global_min_withdrawal":
        msg = bot.edit_message_text("💸 सभी users के लिए Minimum Withdrawal amount enter करें (रुपये में):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "edit_global_min_withdrawal", "message_id": msg.message_id}
    
    elif call.data == "admin_edit_global_ref_reward":
        msg = bot.edit_message_text("🔗 सभी users के लिए Referral Reward enter करें (रुपये में):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "edit_global_ref_reward", "message_id": msg.message_id}
    
    elif call.data == "admin_edit_global_milestone_count":
        msg = bot.edit_message_text("🎯 सभी users के लिए Milestone Count enter करें (संख्या में):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "edit_global_milestone_count", "message_id": msg.message_id}
    
    elif call.data == "admin_edit_global_milestone_reward":
        msg = bot.edit_message_text("🎁 सभी users के लिए Milestone Reward enter करें (रुपये में):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "edit_global_milestone_reward", "message_id": msg.message_id}
    
    elif call.data == "admin_edit_global_welcome_bonus":
        msg = bot.edit_message_text("🎉 सभी users के लिए Welcome Bonus enter करें (रुपये में):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "edit_global_welcome_bonus", "message_id": msg.message_id}
    
    elif call.data == "admin_msg_single":
        msg = bot.edit_message_text("👤 **Send Message to Single User**\n\nUser ID enter करें जिसे message भेजना है:", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        admin_state[ADMIN_ID] = {"action": "msg_single_get_user", "message_id": msg.message_id}
    
    elif call.data == "admin_msg_broadcast":
        msg = bot.edit_message_text("📢 **Broadcast Message to All Users**\n\nवह message type करें जो सभी users को भेजना है:", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        admin_state[ADMIN_ID] = {"action": "msg_broadcast_get_message", "message_id": msg.message_id}
    
    elif call.data == "admin_task_add":
        msg = bot.edit_message_text("➕ **Add New Task**\n\n📝 Task का Title enter करें:", call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        admin_state[ADMIN_ID] = {"action": "task_add_title", "message_id": msg.message_id, "task_data": {}}
    
    elif call.data.startswith("admin_task_view_"):
        page = int(call.data.split("_")[-1])
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        per_page = 5
        total_pages = (len(tasks) - 1) // per_page + 1 if tasks else 0
        start = page * per_page
        end = start + per_page
        
        msg = f"📋 **All Tasks** (Page {page + 1}/{total_pages})\n\n"
        
        for i, task in enumerate(tasks[start:end], start + 1):
            status = "✅ Active" if task.get("active", True) else "❌ Inactive"
            completed = task.get("completed_count", 0)
            quantity = task.get("quantity", 999999)
            msg += f"**{i}. {task['title']}**\n"
            msg += f"   Status: {status}\n"
            msg += f"   Reward: ₹{task['reward']}\n"
            msg += f"   Completed: {completed}/{quantity}\n"
            msg += f"   Link: {task['link'][:30]}...\n\n"
        
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        
        for task in tasks[start:end]:
            edit_btn = types.InlineKeyboardButton(f"✏️ Edit", callback_data=f"admin_task_edit_{task['id']}")
            toggle_btn = types.InlineKeyboardButton(
                "🔄 Toggle" if task.get("active", True) else "🔄 Toggle",
                callback_data=f"admin_task_toggle_{task['id']}"
            )
            delete_btn = types.InlineKeyboardButton(f"🗑 Delete", callback_data=f"admin_task_delete_{task['id']}")
            keyboard.row(edit_btn, toggle_btn, delete_btn)
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton("⬅️ Previous", callback_data=f"admin_task_view_{page - 1}"))
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton("➡️ Next", callback_data=f"admin_task_view_{page + 1}"))
        
        if nav_buttons:
            keyboard.row(*nav_buttons)
        
        back_btn = types.InlineKeyboardButton("🔙 Back to Tasks", callback_data="admin_tasks")
        keyboard.add(back_btn)
        
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
    
    elif call.data.startswith("admin_task_toggle_"):
        task_id = call.data.split("_")[-1]
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        for task in tasks:
            if task["id"] == task_id:
                task["active"] = not task.get("active", True)
                save_bot_data(bot_data)
                status = "Active" if task["active"] else "Inactive"
                bot.answer_callback_query(call.id, f"✅ Task is now {status}!")
                
                if task["active"]:
                    msg_text = f"🔔 **New Task Available!**\n\n📋 {task['title']}\n💰 Reward: ₹{task['reward']}\n\nGet task now: /newtask"
                    success, failed = broadcast_notification(msg_text)
                    bot.send_message(ADMIN_ID, f"📢 Task activated! Notification sent to {success} users")
                
                log_activity(ADMIN_ID, "admin_task_toggled", {"task_id": task_id, "active": task["active"]})
                
                # Refresh the view
                bot_data = get_bot_data()
                tasks = bot_data.get("tasks", [])
                msg = f"🎯 **Task Management**\n\n📋 Total Tasks: {len(tasks)}\n\n"
                
                if tasks:
                    active_tasks = [t for t in tasks if t.get("active", True)]
                    inactive_tasks = [t for t in tasks if not t.get("active", True)]
                    msg += f"✅ Active: {len(active_tasks)}\n❌ Inactive: {len(inactive_tasks)}\n\n"
                    
                    for i, t in enumerate(tasks[:5], 1):
                        st = "✅" if t.get("active", True) else "❌"
                        completed = t.get("completed_count", 0)
                        quantity = t.get("quantity", 999999)
                        msg += f"{i}. {st} {t['title']}\n   Reward: ₹{t['reward']} | Done: {completed}/{quantity}\n\n"
                
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                add_btn = types.InlineKeyboardButton("➕ Add New Task", callback_data="admin_task_add")
                view_btn = types.InlineKeyboardButton("📋 View All Tasks", callback_data="admin_task_view_0")
                keyboard.add(add_btn, view_btn)
                back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
                keyboard.add(back_btn)
                
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
                break
    
    elif call.data.startswith("admin_task_delete_"):
        task_id = call.data.split("_")[-1]
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        for i, task in enumerate(tasks):
            if task["id"] == task_id:
                task_title = task["title"]
                del tasks[i]
                save_bot_data(bot_data)
                bot.answer_callback_query(call.id, f"✅ Task '{task_title}' deleted!")
                log_activity(ADMIN_ID, "admin_task_deleted", {"task_id": task_id, "title": task_title})
                
                # Refresh the view
                bot_data = get_bot_data()
                tasks = bot_data.get("tasks", [])
                msg = f"🎯 **Task Management**\n\n📋 Total Tasks: {len(tasks)}\n\n"
                
                if tasks:
                    active_tasks = [t for t in tasks if t.get("active", True)]
                    inactive_tasks = [t for t in tasks if not t.get("active", True)]
                    msg += f"✅ Active: {len(active_tasks)}\n❌ Inactive: {len(inactive_tasks)}\n\n"
                    
                    for i, t in enumerate(tasks[:5], 1):
                        st = "✅" if t.get("active", True) else "❌"
                        completed = t.get("completed_count", 0)
                        quantity = t.get("quantity", 999999)
                        msg += f"{i}. {st} {t['title']}\n   Reward: ₹{t['reward']} | Done: {completed}/{quantity}\n\n"
                else:
                    msg += "⚠️ No tasks available\n\n"
                
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                add_btn = types.InlineKeyboardButton("➕ Add New Task", callback_data="admin_task_add")
                if tasks:
                    view_btn = types.InlineKeyboardButton("📋 View All Tasks", callback_data="admin_task_view_0")
                    keyboard.add(add_btn, view_btn)
                else:
                    keyboard.add(add_btn)
                back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
                keyboard.add(back_btn)
                
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
                break
    
    elif call.data.startswith("admin_task_edit_"):
        task_id = call.data.split("_")[-1]
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        for task in tasks:
            if task["id"] == task_id:
                msg = f"""✏️ **Edit Task**

📝 Title: {task['title']}
📄 Description: {task['description']}
🔗 Link: {task['link']}
💰 Reward: ₹{task['reward']}
📊 Quantity: {task.get('quantity', 999999)}
✅ Status: {'Active' if task.get('active', True) else 'Inactive'}

Select what to edit:"""
                
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                title_btn = types.InlineKeyboardButton("📝 Title", callback_data=f"admin_task_edit_title_{task_id}")
                desc_btn = types.InlineKeyboardButton("📄 Description", callback_data=f"admin_task_edit_desc_{task_id}")
                link_btn = types.InlineKeyboardButton("🔗 Link", callback_data=f"admin_task_edit_link_{task_id}")
                reward_btn = types.InlineKeyboardButton("💰 Reward", callback_data=f"admin_task_edit_reward_{task_id}")
                qty_btn = types.InlineKeyboardButton("📊 Quantity", callback_data=f"admin_task_edit_qty_{task_id}")
                
                keyboard.add(title_btn, desc_btn)
                keyboard.add(link_btn, reward_btn)
                keyboard.add(qty_btn)
                
                back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_task_view_0")
                keyboard.add(back_btn)
                
                bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode='Markdown')
                break
    
    elif call.data.startswith("admin_task_edit_title_"):
        task_id = call.data.split("_")[-1]
        msg = bot.edit_message_text("📝 नया Task Title enter करें:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "task_edit_title", "task_id": task_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_task_edit_desc_"):
        task_id = call.data.split("_")[-1]
        msg = bot.edit_message_text("📄 नया Task Description enter करें:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "task_edit_desc", "task_id": task_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_task_edit_link_"):
        task_id = call.data.split("_")[-1]
        msg = bot.edit_message_text("🔗 नया Task Link enter करें:", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "task_edit_link", "task_id": task_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_task_edit_reward_"):
        task_id = call.data.split("_")[-1]
        msg = bot.edit_message_text("💰 नया Task Reward enter करें (रुपये में):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "task_edit_reward", "task_id": task_id, "message_id": msg.message_id}
    
    elif call.data.startswith("admin_task_edit_qty_"):
        task_id = call.data.split("_")[-1]
        msg = bot.edit_message_text("📊 नया Task Quantity enter करें (कितने users कर सकते हैं):", call.message.chat.id, call.message.message_id)
        admin_state[ADMIN_ID] = {"action": "task_edit_qty", "task_id": task_id, "message_id": msg.message_id}

def show_users_page(chat_id, message_id, page, per_page):
    users_data = get_all_users_data()
    users_list = list(users_data.items())
    total_users = len(users_list)
    total_pages = (total_users + per_page - 1) // per_page
    
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, total_users)
    
    msg = f"👥 **All Users** (Page {page + 1}/{total_pages})\n\n"
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for user_id, user_data in users_list[start_idx:end_idx]:
        user_name = user_data.get("first_name", "Unknown")
        balance = user_data.get("balance", 0)
        tasks = len(user_data.get("completed_tasks", []))
        
        btn_text = f"{user_name} (ID: {user_id}) - ₹{balance} | {tasks} tasks"
        btn = types.InlineKeyboardButton(btn_text, callback_data=f"admin_view_user_{user_id}")
        keyboard.add(btn)
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton("◀️ Previous", callback_data=f"admin_page_{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(types.InlineKeyboardButton("Next ▶️", callback_data=f"admin_page_{page + 1}"))
    
    if nav_buttons:
        keyboard.row(*nav_buttons)
    
    back_btn = types.InlineKeyboardButton("🔙 Back to Menu", callback_data="admin_back")
    keyboard.add(back_btn)
    
    bot.edit_message_text(msg, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

def show_user_details(chat_id, message_id, user_id):
    user_data = get_user_data(user_id)
    
    if not user_data:
        bot.edit_message_text("❌ User not found", chat_id, message_id)
        return
    
    bot_data = get_bot_data()
    settings = bot_data.get("settings", {})
    
    custom_ref_reward = get_user_custom_setting(user_id, "referral_reward", None)
    ref_reward_display = f"₹{custom_ref_reward} (Custom)" if custom_ref_reward is not None else f"₹{settings.get('referral_reward', REFERRAL_REWARD)} (Default)"
    
    custom_milestone_count = get_user_custom_setting(user_id, "milestone_count", None)
    milestone_count_display = f"{custom_milestone_count} (Custom)" if custom_milestone_count is not None else f"{settings.get('referral_milestone_count', REFERRAL_MILESTONE_COUNT)} (Default)"
    
    custom_milestone_reward = get_user_custom_setting(user_id, "milestone_reward", None)
    milestone_reward_display = f"₹{custom_milestone_reward} (Custom)" if custom_milestone_reward is not None else f"₹{settings.get('referral_milestone_reward', REFERRAL_MILESTONE_REWARD)} (Default)"
    
    custom_welcome_bonus = get_user_custom_setting(user_id, "welcome_bonus", None)
    welcome_bonus_display = f"₹{custom_welcome_bonus} (Custom)" if custom_welcome_bonus is not None else f"₹{settings.get('default_welcome_bonus', DEFAULT_WELCOME_BONUS)} (Default)"
    
    join_date = datetime.fromtimestamp(user_data.get("joined_at", 0)).strftime('%Y-%m-%d %H:%M')
    
    msg = f"""👤 **User Details**

**Basic Info:**
• ID: `{user_id}`
• Name: {user_data.get('first_name', 'N/A')}
• Username: @{user_data.get('username', 'N/A')}
• Language: {user_data.get('language', 'hindi')}
• Joined: {join_date}

**Balance & Earnings:**
• Current Balance: ₹{user_data.get('balance', 0)}
• Total Earnings: ₹{user_data.get('total_earnings', 0)}

**Activity:**
• Completed Tasks: {len(user_data.get('completed_tasks', []))}
• Referrals: {user_data.get('referrals', 0)}
• Referred By: {user_data.get('referred_by', 'None')}

**Custom Settings:**
• Referral Reward: {ref_reward_display}
• Milestone Count: {milestone_count_display}
• Milestone Reward: {milestone_reward_display}
• Welcome Bonus: {welcome_bonus_display}"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    edit_btn = types.InlineKeyboardButton("✏️ Edit Settings", callback_data=f"admin_edit_user_{user_id}")
    back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_users_list")
    keyboard.add(edit_btn)
    keyboard.add(back_btn)
    
    bot.edit_message_text(msg, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

def show_user_edit_options(chat_id, message_id, user_id):
    msg = f"✏️ **Edit User Settings**\n\nUser ID: `{user_id}`\n\nक्या edit करना चाहते हैं?"
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btn1 = types.InlineKeyboardButton("💰 Set Referral Reward", callback_data=f"admin_set_ref_reward_{user_id}")
    btn2 = types.InlineKeyboardButton("🎯 Set Milestone Count", callback_data=f"admin_set_milestone_count_{user_id}")
    btn3 = types.InlineKeyboardButton("🎁 Set Milestone Reward", callback_data=f"admin_set_milestone_reward_{user_id}")
    btn4 = types.InlineKeyboardButton("🎉 Set Welcome Bonus", callback_data=f"admin_set_welcome_bonus_{user_id}")
    btn5 = types.InlineKeyboardButton("➕ Add Balance", callback_data=f"admin_add_balance_{user_id}")
    btn6 = types.InlineKeyboardButton("➖ Deduct Balance", callback_data=f"admin_deduct_balance_{user_id}")
    back_btn = types.InlineKeyboardButton("🔙 Back", callback_data=f"admin_view_user_{user_id}")
    
    keyboard.add(btn1, btn2, btn3, btn4, btn5, btn6, back_btn)
    
    bot.edit_message_text(msg, chat_id, message_id, reply_markup=keyboard, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and ADMIN_ID in admin_state)
def handle_admin_input(message):
    state = admin_state.get(ADMIN_ID)
    if not state:
        return
    
    action = state.get("action")
    
    if action == "search_user":
        try:
            user_id = int(message.text.strip())
            if user_exists(user_id):
                bot.delete_message(message.chat.id, message.message_id)
                show_user_details(message.chat.id, state["message_id"], user_id)
            else:
                bot.send_message(ADMIN_ID, f"❌ User ID {user_id} not found")
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid User ID")
        del admin_state[ADMIN_ID]
    
    elif action == "set_ref_reward":
        user_id = state["user_id"]
        try:
            if message.text.strip().lower() == "default":
                set_user_custom_setting(user_id, "referral_reward", None)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Referral Reward default पर set हो गया")
            else:
                amount = float(message.text.strip())
                set_user_custom_setting(user_id, "referral_reward", amount)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Referral Reward ₹{amount} set हो गया")
            log_activity(ADMIN_ID, "admin_set_referral_reward", {"user_id": user_id, "amount": amount if message.text.strip().lower() != "default" else "default"})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount")
        del admin_state[ADMIN_ID]
    
    elif action == "set_milestone_count":
        user_id = state["user_id"]
        try:
            if message.text.strip().lower() == "default":
                set_user_custom_setting(user_id, "milestone_count", None)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Milestone Count default पर set हो गया")
            else:
                count = int(message.text.strip())
                set_user_custom_setting(user_id, "milestone_count", count)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Milestone Count {count} set हो गया")
            log_activity(ADMIN_ID, "admin_set_milestone_count", {"user_id": user_id, "count": count if message.text.strip().lower() != "default" else "default"})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid number")
        del admin_state[ADMIN_ID]
    
    elif action == "set_milestone_reward":
        user_id = state["user_id"]
        try:
            if message.text.strip().lower() == "default":
                set_user_custom_setting(user_id, "milestone_reward", None)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Milestone Reward default पर set हो गया")
            else:
                amount = float(message.text.strip())
                set_user_custom_setting(user_id, "milestone_reward", amount)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Milestone Reward ₹{amount} set हो गया")
            log_activity(ADMIN_ID, "admin_set_milestone_reward", {"user_id": user_id, "amount": amount if message.text.strip().lower() != "default" else "default"})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount")
        del admin_state[ADMIN_ID]
    
    elif action == "set_welcome_bonus":
        user_id = state["user_id"]
        try:
            if message.text.strip().lower() == "default":
                set_user_custom_setting(user_id, "welcome_bonus", None)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Welcome Bonus default पर set हो गया")
            else:
                amount = float(message.text.strip())
                set_user_custom_setting(user_id, "welcome_bonus", amount)
                bot.send_message(ADMIN_ID, f"✅ User {user_id} का Welcome Bonus ₹{amount} set हो गया")
            log_activity(ADMIN_ID, "admin_set_welcome_bonus", {"user_id": user_id, "amount": amount if message.text.strip().lower() != "default" else "default"})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount")
        del admin_state[ADMIN_ID]
    
    elif action == "add_balance":
        user_id = state["user_id"]
        try:
            amount = float(message.text.strip())
            add_user_balance(user_id, amount)
            bot.send_message(ADMIN_ID, f"✅ User {user_id} के balance में ₹{amount} add हो गया")
            log_activity(ADMIN_ID, "admin_add_balance", {"user_id": user_id, "amount": amount})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount")
        del admin_state[ADMIN_ID]
    
    elif action == "deduct_balance":
        user_id = state["user_id"]
        try:
            amount = float(message.text.strip())
            deduct_user_balance(user_id, amount)
            bot.send_message(ADMIN_ID, f"✅ User {user_id} के balance से ₹{amount} deduct हो गया")
            log_activity(ADMIN_ID, "admin_deduct_balance", {"user_id": user_id, "amount": amount})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount")
        del admin_state[ADMIN_ID]
    
    elif action == "search_user_for_referral":
        try:
            user_id = int(message.text.strip())
            if user_exists(user_id):
                bot.delete_message(message.chat.id, message.message_id)
                show_user_edit_options(message.chat.id, state["message_id"], user_id)
            else:
                bot.send_message(ADMIN_ID, f"❌ User ID {user_id} not found")
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid User ID")
        del admin_state[ADMIN_ID]
    
    elif action == "search_user_for_balance":
        try:
            user_id = int(message.text.strip())
            if user_exists(user_id):
                bot.delete_message(message.chat.id, message.message_id)
                user_data = get_user_data(user_id)
                
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                add_btn = types.InlineKeyboardButton("➕ Add Balance", callback_data=f"admin_add_balance_{user_id}")
                deduct_btn = types.InlineKeyboardButton("➖ Deduct Balance", callback_data=f"admin_deduct_balance_{user_id}")
                back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
                keyboard.add(add_btn, deduct_btn)
                keyboard.add(back_btn)
                
                msg = f"""💰 **Adjust Balance**

User ID: `{user_id}`
Name: {user_data.get('first_name', 'N/A')}
Current Balance: ₹{user_data.get('balance', 0)}

Choose action:"""
                
                bot.edit_message_text(msg, message.chat.id, state["message_id"], reply_markup=keyboard, parse_mode='Markdown')
            else:
                bot.send_message(ADMIN_ID, f"❌ User ID {user_id} not found")
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid User ID")
        del admin_state[ADMIN_ID]
    
    elif action == "search_user_for_block":
        try:
            user_id = int(message.text.strip())
            if user_exists(user_id):
                bot.delete_message(message.chat.id, message.message_id)
                user_data = get_user_data(user_id)
                is_blocked = is_user_blocked(user_id)
                
                keyboard = types.InlineKeyboardMarkup()
                if is_blocked:
                    action_btn = types.InlineKeyboardButton("✅ Unblock User", callback_data=f"admin_unblock_{user_id}")
                else:
                    action_btn = types.InlineKeyboardButton("🚫 Block User", callback_data=f"admin_block_{user_id}")
                back_btn = types.InlineKeyboardButton("🔙 Back", callback_data="admin_refresh")
                keyboard.add(action_btn)
                keyboard.add(back_btn)
                
                status = "🚫 Blocked" if is_blocked else "✅ Active"
                msg = f"""🚫 **Block/Unblock User**

User ID: `{user_id}`
Name: {user_data.get('first_name', 'N/A')}
Status: {status}

Choose action:"""
                
                bot.edit_message_text(msg, message.chat.id, state["message_id"], reply_markup=keyboard, parse_mode='Markdown')
            else:
                bot.send_message(ADMIN_ID, f"❌ User ID {user_id} not found")
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid User ID")
        del admin_state[ADMIN_ID]
    
    elif action == "edit_global_min_withdrawal":
        try:
            amount = float(message.text.strip())
            bot_data = get_bot_data()
            if "settings" not in bot_data:
                bot_data["settings"] = {}
            bot_data["settings"]["min_withdrawal"] = amount
            save_bot_data(bot_data)
            bot.send_message(ADMIN_ID, f"✅ सभी users के लिए Minimum Withdrawal ₹{amount} set हो गया!\n\nअब सभी नए withdrawals के लिए यह limit apply होगी।")
            log_activity(ADMIN_ID, "admin_edit_global_min_withdrawal", {"amount": amount})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount. कृपया सही राशि enter करें।")
        del admin_state[ADMIN_ID]
    
    elif action == "edit_global_ref_reward":
        try:
            amount = float(message.text.strip())
            bot_data = get_bot_data()
            if "settings" not in bot_data:
                bot_data["settings"] = {}
            bot_data["settings"]["referral_reward"] = amount
            save_bot_data(bot_data)
            bot.send_message(ADMIN_ID, f"✅ सभी users के लिए Referral Reward ₹{amount} set हो गया!\n\nअब हर नए referral पर यह amount मिलेगा (जिन users के custom settings नहीं हैं)।")
            
            msg_text = f"🔔 **Referral Reward Updated!**\n\n💰 New reward: ₹{amount} per referral\n\n🔗 Share your link: /refer"
            success, failed = broadcast_notification(msg_text)
            bot.send_message(ADMIN_ID, f"📢 Notification sent to users!\n✅ Success: {success}\n❌ Failed: {failed}")
            
            log_activity(ADMIN_ID, "admin_edit_global_ref_reward", {"amount": amount, "notified": success})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount. कृपया सही राशि enter करें।")
        del admin_state[ADMIN_ID]
    
    elif action == "edit_global_milestone_count":
        try:
            count = int(message.text.strip())
            bot_data = get_bot_data()
            if "settings" not in bot_data:
                bot_data["settings"] = {}
            bot_data["settings"]["referral_milestone_count"] = count
            save_bot_data(bot_data)
            bot.send_message(ADMIN_ID, f"✅ सभी users के लिए Milestone Count {count} set हो गया!\n\nअब हर {count} referrals पर milestone bonus मिलेगा।")
            
            msg_text = f"🔔 **Milestone Updated!**\n\n🎯 New milestone: Every {count} referrals\n\n🔗 Check progress: /refer"
            success, failed = broadcast_notification(msg_text)
            bot.send_message(ADMIN_ID, f"📢 Notification sent!\n✅ Success: {success}\n❌ Failed: {failed}")
            
            log_activity(ADMIN_ID, "admin_edit_global_milestone_count", {"count": count, "notified": success})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid number. कृपया सही संख्या enter करें।")
        del admin_state[ADMIN_ID]
    
    elif action == "edit_global_milestone_reward":
        try:
            amount = float(message.text.strip())
            bot_data = get_bot_data()
            if "settings" not in bot_data:
                bot_data["settings"] = {}
            bot_data["settings"]["referral_milestone_reward"] = amount
            save_bot_data(bot_data)
            bot.send_message(ADMIN_ID, f"✅ सभी users के लिए Milestone Reward ₹{amount} set हो गया!\n\नअब milestone complete होने पर यह bonus मिलेगा।")
            
            msg_text = f"🔔 **Milestone Reward Updated!**\n\n🏆 New bonus: ₹{amount}\n\n🔗 Start referring: /refer"
            success, failed = broadcast_notification(msg_text)
            bot.send_message(ADMIN_ID, f"📢 Notification sent!\n✅ Success: {success}\n❌ Failed: {failed}")
            
            log_activity(ADMIN_ID, "admin_edit_global_milestone_reward", {"amount": amount, "notified": success})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount. कृपया सही राशि enter करें।")
        del admin_state[ADMIN_ID]
    
    elif action == "edit_global_welcome_bonus":
        try:
            amount = float(message.text.strip())
            bot_data = get_bot_data()
            if "settings" not in bot_data:
                bot_data["settings"] = {}
            bot_data["settings"]["default_welcome_bonus"] = amount
            save_bot_data(bot_data)
            bot.send_message(ADMIN_ID, f"✅ सभी users के लिए Welcome Bonus ₹{amount} set हो गया!\n\nअब हर नए user को यह welcome bonus मिलेगा।")
            
            msg_text = f"🔔 **Welcome Bonus Updated!**\n\n🎁 New users get ₹{amount} bonus!\n\n🔗 Share your link: /refer"
            success, failed = broadcast_notification(msg_text)
            bot.send_message(ADMIN_ID, f"📢 Notification sent!\n✅ Success: {success}\n❌ Failed: {failed}")
            
            log_activity(ADMIN_ID, "admin_edit_global_welcome_bonus", {"amount": amount, "notified": success})
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid amount. कृपया सही राशि enter करें।")
        del admin_state[ADMIN_ID]
    
    elif action == "msg_single_get_user":
        try:
            user_id = int(message.text.strip())
            if user_exists(user_id):
                bot.delete_message(message.chat.id, message.message_id)
                user_data = get_user_data(user_id)
                bot.send_message(ADMIN_ID, f"✅ User मिल गया!\n\n👤 ID: {user_id}\n📝 Name: {user_data.get('first_name', 'N/A')}\n\nअब वह message type करें जो इस user को भेजना है:")
                admin_state[ADMIN_ID] = {"action": "msg_single_send", "user_id": user_id}
            else:
                bot.send_message(ADMIN_ID, f"❌ User ID {user_id} not found. कृपया सही User ID enter करें।")
                del admin_state[ADMIN_ID]
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid User ID. कृपया सही number enter करें।")
            del admin_state[ADMIN_ID]
    
    elif action == "msg_single_send":
        user_id = state["user_id"]
        message_text = message.text.strip()
        
        try:
            bot.send_message(user_id, f"📩 **Message from Admin**\n\n{message_text}", parse_mode='Markdown')
            bot.send_message(ADMIN_ID, f"✅ Message successfully sent!\n\n👤 User ID: {user_id}\n📝 Message: {message_text}")
            log_activity(ADMIN_ID, "admin_message_single", {"user_id": user_id, "message": message_text[:100]})
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Message send करने में error आई:\n{str(e)}")
        del admin_state[ADMIN_ID]
    
    elif action == "msg_broadcast_get_message":
        message_text = message.text.strip()
        bot.delete_message(message.chat.id, message.message_id)
        
        users_data = get_all_users_data()
        total_users = len(users_data)
        
        bot.send_message(ADMIN_ID, f"📢 Broadcast शुरू हो रहा है...\n\n👥 Total Users: {total_users}\n📝 Message: {message_text}\n\n⏳ कृपया थोड़ा wait करें...")
        
        success_count = 0
        failed_count = 0
        blocked_count = 0
        
        for user_id_str in users_data.keys():
            try:
                user_id = int(user_id_str)
                if is_user_blocked(user_id):
                    blocked_count += 1
                    continue
                
                bot.send_message(user_id, f"📢 **Broadcast Message**\n\n{message_text}", parse_mode='Markdown')
                success_count += 1
                time.sleep(0.05)
            except Exception as e:
                failed_count += 1
        
        summary = f"""✅ **Broadcast Complete!**

📊 Statistics:
• Total Users: {total_users}
• ✅ Sent Successfully: {success_count}
• ❌ Failed: {failed_count}
• 🚫 Blocked Users: {blocked_count}

📝 Message: {message_text[:100]}"""
        
        bot.send_message(ADMIN_ID, summary)
        log_activity(ADMIN_ID, "admin_broadcast", {"total_users": total_users, "success": success_count, "failed": failed_count, "blocked": blocked_count, "message": message_text[:100]})
        del admin_state[ADMIN_ID]
    
    elif action == "task_add_title":
        state["task_data"]["title"] = message.text.strip()
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, "📄 अब Task का Description enter करें:")
        admin_state[ADMIN_ID]["action"] = "task_add_desc"
    
    elif action == "task_add_desc":
        state["task_data"]["description"] = message.text.strip()
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, "🔗 अब Task का Link enter करें:")
        admin_state[ADMIN_ID]["action"] = "task_add_link"
    
    elif action == "task_add_link":
        state["task_data"]["link"] = message.text.strip()
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(ADMIN_ID, "💰 अब Task का Reward enter करें (रुपये में):")
        admin_state[ADMIN_ID]["action"] = "task_add_reward"
    
    elif action == "task_add_reward":
        try:
            reward = float(message.text.strip())
            state["task_data"]["reward"] = reward
            bot.delete_message(message.chat.id, message.message_id)
            bot.send_message(ADMIN_ID, "📊 अब Task की Quantity enter करें (कितने users कर सकते हैं):")
            admin_state[ADMIN_ID]["action"] = "task_add_qty"
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid reward amount. कृपया सही राशि enter करें।")
    
    elif action == "task_add_qty":
        try:
            quantity = int(message.text.strip())
            task_data = state["task_data"]
            task_data["quantity"] = quantity
            task_data["id"] = str(uuid.uuid4())
            task_data["active"] = True
            task_data["completed_count"] = 0
            task_data["created_at"] = time.time()
            
            bot_data = get_bot_data()
            if "tasks" not in bot_data:
                bot_data["tasks"] = []
            bot_data["tasks"].append(task_data)
            save_bot_data(bot_data)
            
            bot.send_message(ADMIN_ID, f"""✅ **Task Successfully Added!**

📝 Title: {task_data['title']}
📄 Description: {task_data['description']}
🔗 Link: {task_data['link']}
💰 Reward: ₹{task_data['reward']}
📊 Quantity: {task_data['quantity']}
✅ Status: Active

Task अब users को available है!""")
            
            msg_text = f"🔔 **New Task Available!**\n\n📋 {task_data['title']}\n📝 {task_data['description']}\n💰 Reward: ₹{task_data['reward']}\n\nGet task now: /newtask"
            success, failed = broadcast_notification(msg_text)
            bot.send_message(ADMIN_ID, f"📢 Notification sent to users!\n✅ Success: {success}\n❌ Failed: {failed}")
            
            log_activity(ADMIN_ID, "admin_task_added", {"task_id": task_data["id"], "title": task_data["title"], "reward": task_data["reward"], "notified": success})
            del admin_state[ADMIN_ID]
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid quantity. कृपया सही संख्या enter करें।")
    
    elif action == "task_edit_title":
        task_id = state["task_id"]
        new_title = message.text.strip()
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        for task in tasks:
            if task["id"] == task_id:
                old_title = task["title"]
                task["title"] = new_title
                save_bot_data(bot_data)
                bot.send_message(ADMIN_ID, f"✅ Task title updated!\n\nOld: {old_title}\nNew: {new_title}")
                log_activity(ADMIN_ID, "admin_task_edited", {"task_id": task_id, "field": "title", "new_value": new_title})
                break
        del admin_state[ADMIN_ID]
    
    elif action == "task_edit_desc":
        task_id = state["task_id"]
        new_desc = message.text.strip()
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        for task in tasks:
            if task["id"] == task_id:
                task["description"] = new_desc
                save_bot_data(bot_data)
                bot.send_message(ADMIN_ID, f"✅ Task description updated!\n\n{new_desc}")
                log_activity(ADMIN_ID, "admin_task_edited", {"task_id": task_id, "field": "description"})
                break
        del admin_state[ADMIN_ID]
    
    elif action == "task_edit_link":
        task_id = state["task_id"]
        new_link = message.text.strip()
        bot_data = get_bot_data()
        tasks = bot_data.get("tasks", [])
        
        for task in tasks:
            if task["id"] == task_id:
                task["link"] = new_link
                save_bot_data(bot_data)
                bot.send_message(ADMIN_ID, f"✅ Task link updated!\n\n{new_link}")
                log_activity(ADMIN_ID, "admin_task_edited", {"task_id": task_id, "field": "link"})
                break
        del admin_state[ADMIN_ID]
    
    elif action == "task_edit_reward":
        try:
            task_id = state["task_id"]
            new_reward = float(message.text.strip())
            bot_data = get_bot_data()
            tasks = bot_data.get("tasks", [])
            
            for task in tasks:
                if task["id"] == task_id:
                    old_reward = task["reward"]
                    task["reward"] = new_reward
                    save_bot_data(bot_data)
                    bot.send_message(ADMIN_ID, f"✅ Task reward updated!\n\nOld: ₹{old_reward}\nNew: ₹{new_reward}")
                    log_activity(ADMIN_ID, "admin_task_edited", {"task_id": task_id, "field": "reward", "new_value": new_reward})
                    break
            del admin_state[ADMIN_ID]
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid reward amount. कृपया सही राशि enter करें।")
            del admin_state[ADMIN_ID]
    
    elif action == "task_edit_qty":
        try:
            task_id = state["task_id"]
            new_qty = int(message.text.strip())
            bot_data = get_bot_data()
            tasks = bot_data.get("tasks", [])
            
            for task in tasks:
                if task["id"] == task_id:
                    old_qty = task.get("quantity", 999999)
                    task["quantity"] = new_qty
                    save_bot_data(bot_data)
                    bot.send_message(ADMIN_ID, f"✅ Task quantity updated!\n\nOld: {old_qty}\nNew: {new_qty}")
                    log_activity(ADMIN_ID, "admin_task_edited", {"task_id": task_id, "field": "quantity", "new_value": new_qty})
                    break
            del admin_state[ADMIN_ID]
        except:
            bot.send_message(ADMIN_ID, "❌ Invalid quantity. कृपया सही संख्या enter करें।")
            del admin_state[ADMIN_ID]

@bot.message_handler(func=lambda message: message.text and message.text.startswith("🌐"))
def language_command(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        return
    if not user_exists(user_id):
        bot.reply_to(message, get_message("hindi", "start_first"))
        return
    user_language = get_user_language(user_id)
    keyboard = get_language_keyboard()
    bot.send_message(user_id, get_message(user_language, "select_language"), reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language_selection(call):
    user_id = call.from_user.id
    language = call.data.split("_")[1]
    set_user_language(user_id, language)
    bot.edit_message_text(get_message(language, "language_changed"), chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.send_message(user_id, get_message(language, "menu_text"))
    log_activity(user_id, "language_changed", {"language": language})

@bot.message_handler(func=lambda message: message.text and (message.text.startswith("🎯") or message.text == "🎯 New Task"))
@bot.message_handler(commands=['newtask'])
def new_task_command(message):
    user_id = message.from_user.id
    if is_user_blocked(user_id):
        user_language = get_user_language(user_id)
        bot.reply_to(message, get_message(user_language, "user_blocked"))
        return
    tasks = get_bot_data().get("tasks", [])
    user_data = get_user_data(user_id)
    completed_tasks = user_data.get("completed_tasks", [])
    available_task = None
    for task in tasks:
        if task["id"] not in completed_tasks:
            if task.get("active", True):
                completed_count = task.get("completed_count", 0)
                quantity = task.get("quantity", 999999)
                if completed_count < quantity:
                    available_task = task
                    break
    user_language = get_user_language(user_id)
    if not available_task:
        bot.reply_to(message, get_message(user_language, "no_tasks"))
        return
    current_task = user_data.get("current_task")
    if current_task == available_task["id"]:
        bot.reply_to(message, get_message(user_language, "task_already_active"))
        return
    set_user_current_task(user_id, available_task["id"])
    task_message = get_message(user_language, "task_assigned", title=available_task['title'], description=available_task['description'], link=available_task['link'], reward=available_task['reward'])
    bot.reply_to(message, task_message)
    log_activity(user_id, "task_requested", {"task_id": available_task["id"]})

@bot.message_handler(func=lambda message: message.text and message.text.startswith("💰"))
@bot.message_handler(commands=['balance'])
def balance_command(message):
    user_id = message.from_user.id
    user_language = get_user_language(user_id)
    if is_user_blocked(user_id):
        bot.reply_to(message, get_message(user_language, "user_blocked"))
        return
    user_data = get_user_data(user_id)
    if not user_data:
        bot.reply_to(message, get_message(user_language, "start_first"))
        return
    total_earnings = user_data.get('total_earnings', 0)
    current_balance = user_data.get('balance', 0)
    completed_tasks = len(user_data.get('completed_tasks', []))
    referrals = user_data.get('referrals', 0)
    balance_message = get_message(user_language, "balance_info", balance=current_balance, total_earnings=total_earnings, completed_tasks=completed_tasks, referrals=referrals)
    bot.reply_to(message, balance_message)
    log_activity(user_id, "balance_checked", {"balance": current_balance})

@bot.message_handler(func=lambda message: message.text and message.text.startswith("💸"))
@bot.message_handler(commands=['withdrawal'])
def withdrawal_command(message):
    user_id = message.from_user.id
    user_language = get_user_language(user_id)
    if is_user_blocked(user_id):
        bot.reply_to(message, get_message(user_language, "user_blocked"))
        return
    user_data = get_user_data(user_id)
    if not user_data:
        bot.reply_to(message, get_message(user_language, "start_first"))
        return
    bot_data = get_bot_data()
    settings = bot_data.get("settings", {})
    min_withdrawal = settings.get("min_withdrawal", MINIMUM_WITHDRAWAL)
    balance = user_data.get('balance', 0)
    if balance < min_withdrawal:
        bot.reply_to(message, get_message(user_language, "insufficient_balance", balance=balance, min_withdrawal=min_withdrawal))
        return
    msg = bot.reply_to(message, get_message(user_language, "enter_upi"))
    bot.register_next_step_handler(msg, process_upi_id, balance)
    log_activity(user_id, "withdrawal_initiated", {"balance": balance})

def process_upi_id(message, balance):
    user_id = message.from_user.id
    upi_id = message.text.strip()
    user_language = get_user_language(user_id)
    if "@" not in upi_id or len(upi_id) < 10:
        bot.reply_to(message, get_message(user_language, "invalid_format"))
        return
    withdrawal_request = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": balance,
        "upi_id": upi_id,
        "timestamp": time.time(),
        "status": "pending"
    }
    add_withdrawal_request(withdrawal_request)
    deduct_user_balance(user_id, balance)
    bot.reply_to(message, get_message(user_language, "withdrawal_submitted", amount=balance, upi_id=upi_id))
    admin_message = f"""💸 नया निकासी अनुरोध

👤 User ID: {user_id}
💰 Amount: ₹{balance}
💳 UPI ID: {upi_id}
🕐 Time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Request ID: {withdrawal_request['id']}"""
    keyboard = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ Approve Payment", callback_data=f"approve_withdrawal_{withdrawal_request['id']}")
    reject_btn = types.InlineKeyboardButton("❌ Reject & Refund", callback_data=f"reject_withdrawal_{withdrawal_request['id']}")
    keyboard.add(approve_btn, reject_btn)
    try:
        bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard)
    except:
        pass
    log_activity(user_id, "withdrawal_requested", {"amount": balance, "upi_id": upi_id, "request_id": withdrawal_request['id']})

@bot.message_handler(func=lambda message: message.text and message.text.startswith("🔗"))
@bot.message_handler(commands=['refer'])
def refer_command(message):
    user_id = message.from_user.id
    user_language = get_user_language(user_id)
    if is_user_blocked(user_id):
        bot.reply_to(message, get_message(user_language, "user_blocked"))
        return
    user_data = get_user_data(user_id)
    if not user_data:
        bot.reply_to(message, get_message(user_language, "start_first"))
        return
    bot_data = get_bot_data()
    settings = bot_data.get("settings", {})
    bot_username = settings.get("bot_username", BOT_USERNAME)
    
    user_ref_reward = get_user_custom_setting(user_id, "referral_reward", None)
    if user_ref_reward is not None:
        referral_reward = user_ref_reward
    else:
        referral_reward = settings.get("referral_reward", REFERRAL_REWARD)
    
    user_milestone_count = get_user_custom_setting(user_id, "milestone_count", None)
    if user_milestone_count is not None:
        referral_milestone_count = user_milestone_count
    else:
        referral_milestone_count = settings.get("referral_milestone_count", REFERRAL_MILESTONE_COUNT)
    
    user_milestone_reward = get_user_custom_setting(user_id, "milestone_reward", None)
    if user_milestone_reward is not None:
        referral_milestone_reward = user_milestone_reward
    else:
        referral_milestone_reward = settings.get("referral_milestone_reward", REFERRAL_MILESTONE_REWARD)
    
    referral_link = f"https://t.me/{bot_username}?start={user_id}"
    referrals_count = user_data.get('referrals', 0)
    referral_earnings = referrals_count * referral_reward
    refer_message = get_message(user_language, "referral_info", referral_link=referral_link, referrals_count=referrals_count, referral_earnings=referral_earnings, referral_reward=referral_reward, milestone_count=referral_milestone_count, milestone_reward=referral_milestone_reward)
    bot.reply_to(message, refer_message)
    log_activity(user_id, "referral_link_accessed", {"referrals_count": referrals_count})

@bot.message_handler(func=lambda message: message.text and message.text.startswith("❓"))
@bot.message_handler(commands=['help'])
def help_command(message):
    user_id = message.from_user.id
    user_language = get_user_language(user_id)
    bot_data = get_bot_data()
    settings = bot_data.get("settings", {})
    min_withdrawal = settings.get("min_withdrawal", MINIMUM_WITHDRAWAL)
    help_msg = get_message(user_language, "help", min_withdrawal=min_withdrawal)
    bot.reply_to(message, help_msg)
    log_activity(user_id, "help_accessed", {})

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id
    user_language = get_user_language(user_id)
    if is_user_blocked(user_id):
        bot.reply_to(message, get_message(user_language, "user_blocked"))
        return
    user_data = get_user_data(user_id)
    if not user_data:
        bot.reply_to(message, get_message(user_language, "start_first"))
        return
    current_task_id = user_data.get('current_task')
    if not current_task_id:
        bot.reply_to(message, get_message(user_language, "no_active_task"))
        return
    tasks = get_bot_data().get("tasks", [])
    current_task = None
    for task in tasks:
        if task["id"] == current_task_id:
            current_task = task
            break
    if not current_task:
        bot.reply_to(message, "❌ कार्य नहीं मिला / Task not found")
        return
    if current_task_id in user_data.get('completed_tasks', []):
        bot.reply_to(message, "✅ यह कार्य पहले से पूरा है\n❌ एक कार्य केवल एक बार ही किया जा सकता है")
        clear_user_current_task(user_id)
        return
    admin_message = f"""📸 **स्क्रीनशॉट सत्यापन / Screenshot Verification**

👤 **User Details:**
• ID: {user_id}
• Name: {message.from_user.first_name}
• Username: @{message.from_user.username or 'N/A'}

🎯 **Task Details:**
• Title: {current_task['title']}
• Reward: ₹{current_task['reward']}
• Task ID: {current_task_id}

🕐 Submitted: {time.strftime('%Y-%m-%d %H:%M:%S')}"""
    keyboard = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}_{current_task_id}")
    reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}_{current_task_id}")
    block_btn = types.InlineKeyboardButton("🚫 Block User", callback_data=f"block_{user_id}")
    keyboard.add(approve_btn, reject_btn)
    keyboard.add(block_btn)
    try:
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_message, parse_mode='Markdown', reply_markup=keyboard)
    except:
        pass
    bot.reply_to(message, get_message(user_language, "screenshot_submitted"))
    log_activity(user_id, "screenshot_submitted", {"task_id": current_task_id})

@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_', 'block_', 'approve_withdrawal_', 'reject_withdrawal_')))
def handle_verification_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data.startswith("approve_withdrawal_"):
        request_id = call.data.replace("approve_withdrawal_", "")
        bot_data = get_bot_data()
        withdrawal_requests = bot_data.get("withdrawal_requests", [])
        request = None
        for req in withdrawal_requests:
            if req["id"] == request_id:
                request = req
                break
        if not request:
            bot.edit_message_text("❌ Withdrawal request not found", call.message.chat.id, call.message.message_id)
            return
        update_withdrawal_request_status(request_id, "approved")
        bot.edit_message_text(f"✅ **Withdrawal Approved**\n\n👤 User: {request['user_id']}\n💰 Amount: ₹{request['amount']}\n💳 UPI ID: {request['upi_id']}\n📅 Date: {request['timestamp']}\n✨ Payment approved", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(request['user_id'], f"✅ **निकासी स्वीकृत**\n\n💰 राशि: ₹{request['amount']}\n💳 UPI ID: {request['upi_id']}\n✨ पेमेंट 24-48 घंटे में आपके खाते में आ जाएगी!")
        except:
            pass
        log_activity(ADMIN_ID, "withdrawal_approved", {"request_id": request_id, "user_id": request['user_id'], "amount": request['amount']})
    elif call.data.startswith("reject_withdrawal_"):
        request_id = call.data.replace("reject_withdrawal_", "")
        bot_data = get_bot_data()
        withdrawal_requests = bot_data.get("withdrawal_requests", [])
        request = None
        for req in withdrawal_requests:
            if req["id"] == request_id:
                request = req
                break
        if not request:
            bot.edit_message_text("❌ Withdrawal request not found", call.message.chat.id, call.message.message_id)
            return
        add_user_balance(request['user_id'], request['amount'])
        update_withdrawal_request_status(request_id, "rejected")
        bot.edit_message_text(f"❌ **Withdrawal Rejected**\n\nUser: {request['user_id']}\nAmount: ₹{request['amount']}\nStatus: Rejected and refunded", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(request['user_id'], f"❌ **निकासी अस्वीकृत**\n\n💰 राशि: ₹{request['amount']}\n💸 राशि वापस आपके बैलेंस में जोड़ दी गई है")
        except:
            pass
        log_activity(ADMIN_ID, "withdrawal_rejected", {"request_id": request_id, "user_id": request['user_id'], "amount": request['amount']})
    else:
        action, user_id, *extra = call.data.split('_')
        user_id = int(user_id)
        if action == "approve":
            task_id = extra[0]
            tasks = get_bot_data().get("tasks", [])
            task = None
            for t in tasks:
                if t["id"] == task_id:
                    task = t
                    break
            if not task:
                bot.edit_message_text("❌ Task not found", call.message.chat.id, call.message.message_id)
                return
            add_user_balance(user_id, task["reward"])
            add_completed_task(user_id, task_id)
            clear_user_current_task(user_id)
            bot_data = get_bot_data()
            tasks = bot_data.get("tasks", [])
            for i, t in enumerate(tasks):
                if t["id"] == task_id:
                    tasks[i]["completed_count"] = t.get("completed_count", 0) + 1
                    break
            bot_data["tasks"] = tasks
            save_bot_data(bot_data)
            bot.edit_message_caption(caption=f"✅ **Task Approved**\n\nUser: {user_id}\nTask: {task['title']}\nReward: ₹{task['reward']}\nStatus: Approved", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')
            try:
                bot.send_message(user_id, f"✅ **कार्य स्वीकृत / Task Approved**\n\n🎯 कार्य: {task['title']}\n💰 रिवॉर्ड: ₹{task['reward']}\n✨ आपके खाते में राशि जोड़ दी गई है!", parse_mode='Markdown')
            except:
                pass
            log_activity(user_id, "task_approved", {"task_id": task_id, "reward": task["reward"], "approved_by": ADMIN_ID})
        elif action == "reject":
            task_id = extra[0]
            tasks = get_bot_data().get("tasks", [])
            task = None
            for t in tasks:
                if t["id"] == task_id:
                    task = t
                    break
            if not task:
                bot.edit_message_text("❌ Task not found", call.message.chat.id, call.message.message_id)
                return
            deduct_user_balance(user_id, task["reward"])
            clear_user_current_task(user_id)
            bot.edit_message_caption(caption=f"❌ **Task Rejected**\n\nUser: {user_id}\nTask: {task['title']}\nPenalty: ₹{task['reward']} deducted", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')
            try:
                bot.send_message(user_id, f"❌ **कार्य अस्वीकृत / Task Rejected**\n\n🎯 कार्य: {task['title']}\n💸 दंड: ₹{task['reward']}\n⚠️ नकली स्क्रीनशॉट के लिए राशि काटी गई है", parse_mode='Markdown')
            except:
                pass
            log_activity(user_id, "task_rejected", {"task_id": task_id, "penalty": task["reward"], "rejected_by": ADMIN_ID})
        elif action == "block":
            block_user(user_id)
            bot.edit_message_caption(caption=f"🚫 **User Blocked**\n\nUser ID: {user_id}\nStatus: Blocked by admin", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown')
            try:
                bot.send_message(user_id, "🚫 **खाता बंद / Account Blocked**\n\nआपका खाता नकली स्क्रीनशॉट भेजने के कारण बंद कर दिया गया है।")
            except:
                pass
            log_activity(user_id, "user_blocked", {"blocked_by": ADMIN_ID})

@bot.message_handler(func=lambda message: message.text.startswith('/') and message.text not in ['/start', '/newtask', '/balance', '/withdrawal', '/refer', '/help', '/admin'])
def handle_unknown_commands(message):
    log_activity(message.from_user.id, "unknown_command", {"text": message.text})
    bot.reply_to(message, "❌ यह कमांड मान्य नहीं है / This command is not valid\n\n✅ वैध कमांड / Valid commands:\n• /start - मेनू / Menu\n• 🎯 नया कार्य / New Task\n• 💰 बैलेंस / Balance\n• 💸 निकासी / Withdrawal\n• 🔗 रेफर / Refer\n• ❓ सहायता / Help")

@bot.message_handler(content_types=['text'])
def handle_text_messages(message):
    if not message.text.startswith('/'):
        log_activity(message.from_user.id, "text_message", {"text": message.text[:50]})
        bot.reply_to(message, "📋 मेनू के लिए /start दबाएं या नीचे दिए गए बटन का उपयोग करें\nPress /start for menu or use the buttons below")

def self_ping_loop():
    while True:
        try:
            time.sleep(120)
            try:
                endpoints = ["/ping", "/status", "/alive"]
                for endpoint in endpoints:
                    requests.get(f"http://127.0.0.1:5000{endpoint}", timeout=10)
                    time.sleep(1)
                print(f"Deployment ping: {time.strftime('%H:%M:%S')}")
            except:
                pass
        except:
            pass

def heartbeat_loop():
    while True:
        try:
            time.sleep(240)
            print(f"Heartbeat: {time.strftime('%H:%M:%S')}")
        except:
            time.sleep(60)

if __name__ == "__main__":
    print("🤖 Bot starting...")
    log_activity(0, "bot_started", {"timestamp": time.time()})
    print("🌐 Starting keep-alive server...")
    keep_alive()
    time.sleep(3)
    ping_thread = threading.Thread(target=self_ping_loop, daemon=True)
    ping_thread.start()
    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()
    try:
        bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted successfully")
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ Webhook deletion failed: {e}")
    while True:
        try:
            print("🔄 Starting bot polling...")
            bot.polling(none_stop=True, interval=2, timeout=30)
            break
        except Exception as e:
            error_msg = str(e).lower()
            print(f"❌ Bot error: {e}")
            if "409" in error_msg or "conflict" in error_msg:
                print("🔄 Resolving conflict...")
                try:
                    for i in range(3):
                        bot.delete_webhook(drop_pending_updates=True)
                        time.sleep(3)
                        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1&limit=1", timeout=10)
                        time.sleep(2)
                    print("✅ Conflict resolved, restarting...")
                    time.sleep(15)
                except Exception as clear_error:
                    print(f"Clear error: {clear_error}")
                    time.sleep(20)
            else:
                log_activity(0, "bot_error", {"error": str(e)})
                time.sleep(15)
