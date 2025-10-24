import telebot
from telebot import types
import threading
import time
import requests
import json
import os
import uuid
from datetime import datetime
from flask import Flask, jsonify, render_template_string

# -----------------------------------------------------------------------------
# --------------------------- CONFIGURATION VARIABLES -------------------------
# -----------------------------------------------------------------------------
# Replace with your actual bot token from BotFather
BOT_TOKEN = "7635250199:AAFfFeZYdlhNjlgU3jGRwRdHF_ckRcRhPZk"

# ❗️ IMPORTANT: Replace with your actual Telegram user ID to receive admin notifications.
# HOW TO GET YOUR ID: Start a chat with @userinfobot on Telegram. It will show you your User ID.
ADMIN_ID = 5367009004

# Your bot's username (without the '@')
BOT_USERNAME = "TaskRewardBot"

# Penalty for rejected tasks
REJECTION_PENALTY = 1 # Amount in rupees

# Data file paths
DATA_DIR = "data"
USERS_DATA_FILE = os.path.join(DATA_DIR, "users_data.json")
BOT_DATA_FILE = os.path.join(DATA_DIR, "bot_data.json")
BLOCKED_USERS_FILE = os.path.join(DATA_DIR, "blocked_users.json")
ACTIVITY_LOG_FILE = os.path.join(DATA_DIR, "activity_log.json")

# Maximum number of logs to keep
MAX_LOG_ENTRIES = 10000

# -----------------------------------------------------------------------------
# ----------------------------- BOT INITIALIZATION ----------------------------
# -----------------------------------------------------------------------------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='HTML')
# This Flask app is meant to be run by a WSGI server like Gunicorn
app = Flask(__name__)
# Used to store temporary data for multi-step operations like adding tasks
admin_wizards = {}


# -----------------------------------------------------------------------------
# ------------------------------ LANGUAGE STRINGS -----------------------------
# -----------------------------------------------------------------------------
MESSAGES = {
    "hindi": {
        "welcome": (
            "🎉 <b>स्वागत है! {bot_username} में आपका स्वागत है!</b>\n\n"
            "💰 कार्य पूरे करें और पैसे कमाएं\n"
            "📸 स्क्रीनशॉट भेजकर कार्य सत्यापित करें\n"
            "💵 न्यूनतम निकासी: <b>₹{min_withdrawal}</b>\n"
            "🔗 रेफर करें और <b>₹{referral_reward}</b> प्रति रेफरल पाएं\n\n"
            "नीचे दिए गए बटन का उपयोग करें:"
        ),
        "help": (
            "📚 <b>सहायता केंद्र</b>\n\n"
            "• <b>🎯 नया कार्य</b>: एक नया कार्य प्राप्त करें।\n"
            "• <b>💰 बैलेंस</b>: अपना वर्तमान बैलेंस देखें।\n"
            "• <b>💸 निकासी</b>: अपनी कमाई निकालें।\n"
            "• <b>🔗 रेफर</b>: दोस्तों को आमंत्रित करें और कमाएं।\n"
            "• <b>🌐 भाषा</b>: बॉट की भाषा बदलें।\n\n"
            "किसी भी समस्या के लिए, कृपया एडमिन से संपर्क करें।"
        ),
        "balance_info": (
            "💰 <b>आपका बैलेंस</b>\n\n"
            "💵 उपलब्ध बैलेंस: <b>₹{balance:.2f}</b>\n"
            "📊 कुल कमाई: <b>₹{total_earnings:.2f}</b>\n"
            "🎯 पूर्ण कार्य: <b>{completed_tasks}</b>\n"
            "🔗 रेफरल्स: <b>{referrals}</b>"
        ),
        "referral_info": (
            "🔗 <b>आपका रेफरल लिंक</b>\n\n"
            "<code>{referral_link}</code>\n\n"
            "📊 <b>आंकड़े:</b>\n"
            "• कुल रेफरल्स: <b>{referrals_count}</b>\n\n"
            "🎁 <b>रेफरल रिवार्ड:</b>\n"
            "• प्रत्येक रेफरल पर: <b>₹{referral_reward}</b>\n"
            "• हर <b>{milestone_count}</b> रेफरल पर बोनस: <b>₹{milestone_reward}</b>\n\n"
            "💡 अपने दोस्तों के साथ यह लिंक शेयर करें!"
        ),
        "task_assigned": (
            "✅ <b>कार्य सौंपा गया!</b>\n\n"
            "📋 <b>कार्य:</b> {title}\n"
            "📝 <b>विवरण:</b> {description}\n"
            "🌐 <b>लिंक:</b> <a href='{link}'>यहां क्लिक करें</a>\n"
            "💰 <b>रिवार्ड:</b> ₹{reward}\n\n"
            "📸 कार्य पूरा करने के बाद स्क्रीनशॉट भेजें।"
        ),
        "no_new_task": "😕 क्षमा करें, अभी कोई नया कार्य उपलब्ध नहीं है। कृपया बाद में पुनः प्रयास करें।",
        "task_in_progress": "⏳ आपके पास पहले से ही एक कार्य लंबित है। कृपया पहले उसे पूरा करें।",
        "submit_prompt": "👍 बहुत अच्छा! अब कृपया इस कार्य को पूरा करने का स्क्रीनशॉट भेजें।",
        "no_task_to_submit": "🤔 आपके पास सबमिट करने के लिए कोई सक्रिय कार्य नहीं है। पहले '/newtask' का उपयोग करके एक कार्य प्राप्त करें।",
        "submission_received": "✅ आपका स्क्रीनशॉट मिल गया है और सत्यापन के लिए भेज दिया गया है। अनुमोदन पर आपको सूचित किया जाएगा।",
        "withdrawal_prompt": "💸 कृपया अपनी UPI ID दर्ज करें जिससे आप पैसे निकालना चाहते हैं।",
        "withdrawal_min_error": "❌ निकासी के लिए न्यूनतम बैलेंस ₹{min_withdrawal} होना चाहिए। आपका बैलेंस ₹{balance:.2f} है।",
        "invalid_upi": "🚫 अमान्य UPI ID। कृपया सही प्रारूप में दर्ज करें (उदाहरण: 12345@upi)।",
        "withdrawal_request_sent": "✅ आपका ₹{amount:.2f} का निकासी अनुरोध दर्ज कर लिया गया है। आपके बैलेंस से राशि काट ली गई है। अनुमोदन के बाद यह आपके खाते में जमा हो जाएगा।",
        "lang_select": "🌐 कृपया अपनी भाषा चुनें:",
        "lang_changed": "✅ भाषा को हिंदी में बदल दिया गया है।",
        "user_blocked": "🚫 आपको इस बॉट का उपयोग करने से ब्लॉक कर दिया गया है।",
        "task_approved": "🎉 बधाई हो! आपका कार्य स्वीकृत हो गया है और आपके खाते में ₹{reward} जोड़ दिए गए हैं।",
        "task_rejected": "😔 क्षमा करें, आपका कार्य अस्वीकार कर दिया गया है। आपके खाते से ₹{penalty} काट लिए गए हैं।",
        "new_referral": "🎉 आपको एक नया रेफरल मिला है! आपके खाते में ₹{reward} जोड़ दिए गए हैं।",
        "milestone_bonus": "🎊 वाह! आपने {count} रेफरल पूरे कर लिए हैं! आपके खाते में ₹{bonus} का बोनस जोड़ा गया है।",
        "main_menu_buttons": ["🎯 नया कार्य", "💰 बैलेंस", "💸 निकासी", "🔗 रेफर", "❓ सहायता", "🌐 भाषा"]
    },
    "english": {
        "welcome": (
            "🎉 <b>Welcome to {bot_username}!</b>\n\n"
            "💰 Complete tasks and earn money\n"
            "📸 Verify tasks by sending screenshots\n"
            "💵 Minimum Withdrawal: <b>₹{min_withdrawal}</b>\n"
            "🔗 Refer and earn <b>₹{referral_reward}</b> per referral\n\n"
            "Use the buttons below to navigate:"
        ),
        "help": (
            "📚 <b>Help Center</b>\n\n"
            "• <b>🎯 New Task</b>: Get a new task to complete.\n"
            "• <b>💰 Balance</b>: Check your current balance.\n"
            "• <b>💸 Withdraw</b>: Withdraw your earnings.\n"
            "• <b>🔗 Refer</b>: Invite friends and earn more.\n"
            "• <b>🌐 Language</b>: Change the bot's language.\n\n"
            "For any issues, please contact the admin."
        ),
        "balance_info": (
            "💰 <b>Your Balance</b>\n\n"
            "💵 Available Balance: <b>₹{balance:.2f}</b>\n"
            "📊 Total Earnings: <b>₹{total_earnings:.2f}</b>\n"
            "🎯 Completed Tasks: <b>{completed_tasks}</b>\n"
            "🔗 Referrals: <b>{referrals}</b>"
        ),
        "referral_info": (
            "🔗 <b>Your Referral Link</b>\n\n"
            "<code>{referral_link}</code>\n\n"
            "📊 <b>Statistics:</b>\n"
            "• Total Referrals: <b>{referrals_count}</b>\n\n"
            "🎁 <b>Referral Rewards:</b>\n"
            "• For each referral: <b>₹{referral_reward}</b>\n"
            "• Bonus on every <b>{milestone_count}</b> referrals: <b>₹{milestone_reward}</b>\n\n"
            "💡 Share this link with your friends!"
        ),
        "task_assigned": (
            "✅ <b>Task Assigned!</b>\n\n"
            "📋 <b>Task:</b> {title}\n"
            "📝 <b>Description:</b> {description}\n"
            "🌐 <b>Link:</b> <a href='{link}'>Click Here</a>\n"
            "💰 <b>Reward:</b> ₹{reward}\n\n"
            "📸 Send a screenshot after completing the task."
        ),
        "no_new_task": "😕 Sorry, no new tasks are available right now. Please try again later.",
        "task_in_progress": "⏳ You already have a task in progress. Please complete it first.",
        "submit_prompt": "👍 Great! Now please send the screenshot as proof of completion for this task.",
        "no_task_to_submit": "🤔 You don't have an active task to submit. Get a task first using '/newtask'.",
        "submission_received": "✅ Your screenshot has been received and sent for verification. You will be notified upon approval.",
        "withdrawal_prompt": "💸 Please enter the UPI ID where you want to withdraw the money.",
        "withdrawal_min_error": "❌ Minimum balance for withdrawal is ₹{min_withdrawal}. Your balance is ₹{balance:.2f}.",
        "invalid_upi": "🚫 Invalid UPI ID. Please enter it in the correct format (e.g., 12345@upi).",
        "withdrawal_request_sent": "✅ Your withdrawal request for ₹{amount:.2f} has been registered. The amount has been deducted from your balance. It will be credited to your account after approval.",
        "lang_select": "🌐 Please select your language:",
        "lang_changed": "✅ Language changed to English.",
        "user_blocked": "🚫 You have been blocked from using this bot.",
        "task_approved": "🎉 Congratulations! Your task has been approved and ₹{reward} has been added to your account.",
        "task_rejected": "😔 Sorry, your task has been rejected. ₹{penalty} has been deducted from your account.",
        "new_referral": "🎉 You have a new referral! ₹{reward} has been added to your account.",
        "milestone_bonus": "🎊 Wow! You've completed {count} referrals! A bonus of ₹{bonus} has been added to your account.",
        "main_menu_buttons": ["🎯 New Task", "💰 Balance", "💸 Withdraw", "🔗 Refer", "❓ Help", "🌐 Language"]
    }
}

# -----------------------------------------------------------------------------
# ------------------------- DATABASE HELPER FUNCTIONS -------------------------
# -----------------------------------------------------------------------------
# Thread-safe lock for file operations
file_lock = threading.Lock()

def initialize_data_files():
    """Creates necessary data files and directories if they don't exist."""
    with file_lock:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

        if not os.path.exists(USERS_DATA_FILE):
            with open(USERS_DATA_FILE, 'w') as f:
                json.dump({}, f)

        if not os.path.exists(BLOCKED_USERS_FILE):
            with open(BLOCKED_USERS_FILE, 'w') as f:
                json.dump([], f)

        if not os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, 'w') as f:
                json.dump([], f)

        if not os.path.exists(BOT_DATA_FILE):
            default_bot_data = {
                "tasks": [],
                "withdrawal_requests": [],
                "settings": {
                    "min_withdrawal": 10,
                    "referral_reward": 2,
                    "referral_milestone_count": 5,
                    "referral_milestone_reward": 10,
                    "bot_username": BOT_USERNAME
                }
            }
            with open(BOT_DATA_FILE, 'w') as f:
                json.dump(default_bot_data, f, indent=4)

def load_json_file(filepath):
    """Loads data from a JSON file."""
    with file_lock:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {} if 'users' in filepath else []

def save_json_file(filepath, data):
    """Saves data to a JSON file."""
    with file_lock:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)

def get_user_data(user_id):
    users = load_json_file(USERS_DATA_FILE)
    return users.get(str(user_id))

def update_user_data(user_id, data):
    users = load_json_file(USERS_DATA_FILE)
    users[str(user_id)] = data
    save_json_file(USERS_DATA_FILE, users)

def get_bot_data():
    return load_json_file(BOT_DATA_FILE)

def save_bot_data(data):
    save_json_file(BOT_DATA_FILE, data)

def get_blocked_users():
    return load_json_file(BLOCKED_USERS_FILE)

def block_user(user_id):
    blocked_users = get_blocked_users()
    if user_id not in blocked_users:
        blocked_users.append(user_id)
        save_json_file(BLOCKED_USERS_FILE, blocked_users)
        log_activity(user_id, "user_blocked", {"admin_id": ADMIN_ID})
        return True
    return False

def unblock_user(user_id):
    blocked_users = get_blocked_users()
    if user_id in blocked_users:
        blocked_users.remove(user_id)
        save_json_file(BLOCKED_USERS_FILE, blocked_users)
        log_activity(user_id, "user_unblocked", {"admin_id": ADMIN_ID})
        return True
    return False

def is_user_blocked(user_id):
    return user_id in get_blocked_users()

# -----------------------------------------------------------------------------
# ------------------------------ LOGGING FUNCTION -----------------------------
# -----------------------------------------------------------------------------
def log_activity(user_id, action, data={}):
    """Logs user and system actions to a file."""
    try:
        log_entry = {
            "timestamp": time.time(),
            "datetime": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "data": data
        }
        logs = load_json_file(ACTIVITY_LOG_FILE)
        logs.append(log_entry)
        # Keep the log file from getting too large
        if len(logs) > MAX_LOG_ENTRIES:
            logs = logs[-MAX_LOG_ENTRIES:]
        save_json_file(ACTIVITY_LOG_FILE, logs)
    except Exception as e:
        print(f"Error logging activity: {e}")

# -----------------------------------------------------------------------------
# --------------------------- LANGUAGE & UI FUNCTIONS -------------------------
# -----------------------------------------------------------------------------
def get_user_language(user_id):
    """Gets the user's preferred language, defaulting to Hindi."""
    user_data = get_user_data(user_id)
    return user_data.get("language", "hindi") if user_data else "hindi"

def get_message(user_id, key, **kwargs):
    """Gets a formatted message string in the user's language."""
    language = get_user_language(user_id)
    message_template = MESSAGES.get(language, MESSAGES["english"]).get(key)
    if not message_template:
        return f"Error: Message key '{key}' not found for language '{language}'"
    
    bot_settings = get_bot_data().get("settings", {})
    
    # Add default format values
    format_params = {
        'bot_username': BOT_USERNAME,
        'min_withdrawal': bot_settings.get("min_withdrawal", 10),
        'referral_reward': bot_settings.get("referral_reward", 2),
        'milestone_count': bot_settings.get("referral_milestone_count", 5),
        'milestone_reward': bot_settings.get("referral_milestone_reward", 10),
    }
    format_params.update(kwargs) # User-provided values override defaults
    
    return message_template.format(**format_params)

def get_main_menu_keyboard(user_id):
    """Creates the main menu keyboard with translated buttons."""
    language = get_user_language(user_id)
    buttons = MESSAGES[language]["main_menu_buttons"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(buttons[0], buttons[1])
    keyboard.row(buttons[2], buttons[3])
    keyboard.row(buttons[4], buttons[5])
    return keyboard

def get_language_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hindi"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_english")
    )
    return keyboard

# -----------------------------------------------------------------------------
# ----------------------------- CORE BOT LOGIC --------------------------------
# -----------------------------------------------------------------------------
# Decorator to check if the user is blocked
def block_check(func):
    def wrapper(message):
        user_id = message.from_user.id
        if is_user_blocked(user_id):
            bot.reply_to(message, get_message(user_id, "user_blocked"))
            return
        return func(message)
    return wrapper

@bot.message_handler(commands=['start'])
def start_command(message):
    user = message.from_user
    user_id = user.id
    
    if is_user_blocked(user_id):
        bot.reply_to(message, get_message(user_id, "user_blocked"))
        return

    # User registration
    if not get_user_data(user_id):
        new_user = {
            "id": user_id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": 0.0,
            "total_earnings": 0.0,
            "completed_tasks": [],
            "referrals": 0,
            "referred_by": None,
            "joined_at": time.time(),
            "current_task": None,
            "language": "hindi"
        }

        # Referral handling
        try:
            referrer_id = message.text.split(' ')[1]
            if referrer_id and referrer_id.isdigit() and str(referrer_id) != str(user_id):
                referrer_data = get_user_data(referrer_id)
                if referrer_data:
                    bot_settings = get_bot_data()["settings"]
                    reward = bot_settings["referral_reward"]
                    milestone_count = bot_settings["referral_milestone_count"]
                    milestone_reward = bot_settings["referral_milestone_reward"]
                    
                    referrer_data["balance"] += reward
                    referrer_data["total_earnings"] += reward
                    referrer_data["referrals"] += 1
                    new_user["referred_by"] = int(referrer_id)
                    
                    if referrer_data["referrals"] % milestone_count == 0:
                        referrer_data["balance"] += milestone_reward
                        referrer_data["total_earnings"] += milestone_reward
                        bot.send_message(referrer_id, get_message(referrer_id, "milestone_bonus", count=referrer_data["referrals"], bonus=milestone_reward))
                    
                    update_user_data(referrer_id, referrer_data)
                    bot.send_message(referrer_id, get_message(referrer_id, "new_referral", reward=reward))
                    log_activity(referrer_id, "referral_bonus", {"new_user_id": user_id, "reward": reward})
        except (IndexError, ValueError):
            referrer_id = None # No valid referrer ID found

        update_user_data(user_id, new_user)
        log_activity(user_id, "user_registered", {"referrer": referrer_id})

    # Send welcome message
    keyboard = get_main_menu_keyboard(user_id)
    bot.send_message(user_id, get_message(user_id, "welcome"), reply_markup=keyboard)


@bot.message_handler(func=lambda msg: msg.text in MESSAGES["hindi"]["main_menu_buttons"] or msg.text in MESSAGES["english"]["main_menu_buttons"])
@block_check
def handle_main_menu(message):
    text = message.text
    if text.startswith("🎯"):
        new_task_command(message)
    elif text.startswith("💰"):
        balance_command(message)
    elif text.startswith("💸"):
        withdrawal_command(message)
    elif text.startswith("🔗"):
        refer_command(message)
    elif text.startswith("❓"):
        help_command(message)
    elif text.startswith("🌐"):
        language_command(message)


@bot.message_handler(commands=['newtask'])
@block_check
def new_task_command(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if user_data.get("current_task"):
        bot.reply_to(message, get_message(user_id, "task_in_progress"))
        return

    bot_data = get_bot_data()
    available_tasks = [
        task for task in bot_data.get("tasks", [])
        if task.get("active") and task["id"] not in user_data.get("completed_tasks", []) and task.get("completed_count", 0) < task.get("quantity", float('inf'))
    ]

    if not available_tasks:
        bot.reply_to(message, get_message(user_id, "no_new_task"))
        return

    task = available_tasks[0]
    user_data["current_task"] = task["id"]
    update_user_data(user_id, user_data)

    bot.reply_to(message, get_message(user_id, "task_assigned",
                                     title=task["title"],
                                     description=task["description"],
                                     link=task["link"],
                                     reward=task["reward"]))
    log_activity(user_id, "task_assigned", {"task_id": task["id"]})


@bot.message_handler(content_types=['photo'])
@block_check
def handle_screenshot(message):
    user_id = message.from_user.id
    user = message.from_user
    user_data = get_user_data(user_id)
    
    current_task_id = user_data.get("current_task")
    if not current_task_id:
        bot.reply_to(message, get_message(user_id, "no_task_to_submit"))
        return

    bot_data = get_bot_data()
    task = next((t for t in bot_data.get("tasks", []) if t["id"] == current_task_id), None)
    
    if not task:
        bot.reply_to(message, "Error: Task not found. Please contact admin.")
        user_data["current_task"] = None
        update_user_data(user_id, user_data)
        return

    caption = (
        f"📸 <b>Screenshot Verification</b>\n\n"
        f"<b>User Details:</b>\n"
        f" • ID: <code>{user_id}</code>\n"
        f" • Name: {user.first_name}\n"
        f" • Username: @{user.username}\n\n"
        f"<b>Task Details:</b>\n"
        f" • Title: {task['title']}\n"
        f" • Reward: ₹{task['reward']}\n"
        f" • Task ID: <code>{task['id']}</code>"
    )
    
    callback_data_prefix = f"{user_id}_{task['id']}_{task['reward']}"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("✅ Approve", callback_data=f"approve_{callback_data_prefix}"),
        types.InlineKeyboardButton("❌ Reject", callback_data=f"reject_{callback_data_prefix}")
    )
    keyboard.row(
        types.InlineKeyboardButton("🚫 Block User", callback_data=f"block_{user_id}")
    )
    
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=keyboard)
    bot.reply_to(message, get_message(user_id, "submission_received"))
    log_activity(user_id, "screenshot_submitted", {"task_id": task["id"]})


@bot.message_handler(commands=['balance'])
@block_check
def balance_command(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    bot.reply_to(message, get_message(user_id, "balance_info",
                                     balance=user_data["balance"],
                                     total_earnings=user_data["total_earnings"],
                                     completed_tasks=len(user_data["completed_tasks"]),
                                     referrals=user_data["referrals"]))


@bot.message_handler(commands=['withdrawal'])
@block_check
def withdrawal_command(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    min_withdrawal = get_bot_data()["settings"]["min_withdrawal"]
    
    if user_data["balance"] < min_withdrawal:
        bot.reply_to(message, get_message(user_id, "withdrawal_min_error", balance=user_data["balance"]))
        return

    msg = bot.reply_to(message, get_message(user_id, "withdrawal_prompt"))
    bot.register_next_step_handler(msg, process_upi_step)

def process_upi_step(message):
    try:
        user_id = message.from_user.id
        upi_id = message.text.strip()
        
        if '@' not in upi_id or len(upi_id) < 5:
            bot.reply_to(message, get_message(user_id, "invalid_upi"))
            return

        user_data = get_user_data(user_id)
        amount = user_data["balance"]
        
        user_data["balance"] = 0.0
        update_user_data(user_id, user_data)
        
        bot_data = get_bot_data()
        request = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": amount,
            "upi_id": upi_id,
            "timestamp": time.time(),
            "status": "pending"
        }
        bot_data.setdefault("withdrawal_requests", []).append(request)
        save_bot_data(bot_data)
        
        admin_caption = (
            f"💸 <b>New Withdrawal Request</b>\n\n"
            f" • User ID: <code>{user_id}</code>\n"
            f" • Amount: <b>₹{amount:.2f}</b>\n"
            f" • UPI ID: <code>{upi_id}</code>\n"
            f" • Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f" • Request ID: <code>{request['id']}</code>"
        )
        admin_keyboard = types.InlineKeyboardMarkup()
        admin_keyboard.row(
            types.InlineKeyboardButton("✅ Approve Payment", callback_data=f"pay_approve_{request['id']}"),
            types.InlineKeyboardButton("❌ Reject & Refund", callback_data=f"pay_reject_{request['id']}_{user_id}_{amount}")
        )
        bot.send_message(ADMIN_ID, admin_caption, reply_markup=admin_keyboard)
        
        bot.reply_to(message, get_message(user_id, "withdrawal_request_sent", amount=amount))
        log_activity(user_id, "withdrawal_request", {"amount": amount, "upi_id": upi_id})

    except Exception as e:
        bot.reply_to(message, "An error occurred. Please try again.")
        print(f"Error in process_upi_step: {e}")

@bot.message_handler(commands=['refer'])
@block_check
def refer_command(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
    bot.reply_to(message, get_message(user_id, "referral_info",
                                     referral_link=referral_link,
                                     referrals_count=user_data["referrals"]))

@bot.message_handler(commands=['help'])
@block_check
def help_command(message):
    user_id = message.from_user.id
    bot.reply_to(message, get_message(user_id, "help"))

@bot.message_handler(commands=['language'])
@block_check
def language_command(message):
    user_id = message.from_user.id
    keyboard = get_language_keyboard()
    bot.reply_to(message, get_message(user_id, "lang_select"), reply_markup=keyboard)


# -----------------------------------------------------------------------------
# ------------------------------ ADMIN PANEL ----------------------------------
# -----------------------------------------------------------------------------

def is_admin(user_id):
    """Checks if a user ID belongs to the admin."""
    return user_id == ADMIN_ID

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "🚫 You are not authorized to use this command.")
        return
    show_admin_menu(message.chat.id)

def show_admin_menu(chat_id, message_id=None):
    text = "👑 <b>Admin Panel</b>\n\nWelcome, admin. Please choose an option:"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("➕ Add Task", callback_data="admin_add_task"),
        types.InlineKeyboardButton("📋 List Tasks", callback_data="admin_list_tasks")
    )
    keyboard.row(
        types.InlineKeyboardButton("📊 Bot Stats", callback_data="admin_stats"),
        types.InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
    )
    keyboard.row(
        types.InlineKeyboardButton("🔓 Unblock User", callback_data="admin_unblock")
    )
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)
    else:
        bot.send_message(chat_id, text, reply_markup=keyboard)

# --- Admin Panel Callback Handlers ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 Unauthorized")
        return

    action = call.data.split('_')[1]
    
    if action == "main":
        show_admin_menu(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if action == "stats":
        show_bot_stats(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)
    
    elif action == "list":
        list_tasks_for_admin(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id)

    elif action == "toggle":
        task_id = call.data.split('_')[2]
        bot_data = get_bot_data()
        task = next((t for t in bot_data.get("tasks", []) if t["id"] == task_id), None)
        if task:
            task["active"] = not task.get("active", False)
            save_bot_data(bot_data)
            bot.answer_callback_query(call.id, f"Task {task_id} status changed.")
            list_tasks_for_admin(call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Error: Task not found.")

    elif action == "delete":
        task_id = call.data.split('_')[2]
        bot_data = get_bot_data()
        initial_len = len(bot_data.get("tasks", []))
        bot_data["tasks"] = [t for t in bot_data.get("tasks", []) if t["id"] != task_id]
        if len(bot_data["tasks"]) < initial_len:
            save_bot_data(bot_data)
            bot.answer_callback_query(call.id, f"Task {task_id} deleted.")
            list_tasks_for_admin(call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "Error: Task not found.")

    elif action == "add":
        start_add_task_wizard(call.message)
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    
    elif action == "broadcast":
        msg = bot.send_message(call.message.chat.id, "📢 Please send the message you want to broadcast to all users. /cancel to abort.")
        bot.register_next_step_handler(msg, process_broadcast_message)
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif action == "unblock":
        msg = bot.send_message(call.message.chat.id, "🔓 Please enter the User ID to unblock. /cancel to abort.")
        bot.register_next_step_handler(msg, process_unblock_user)
        bot.answer_callback_query(call.id)
        bot.delete_message(call.message.chat.id, call.message.message_id)


# --- Admin Panel Functions ---
def show_bot_stats(chat_id, message_id):
    users = load_json_file(USERS_DATA_FILE)
    blocked = load_json_file(BLOCKED_USERS_FILE)
    bot_data = get_bot_data()
    pending_withdrawals = [r for r in bot_data.get("withdrawal_requests", []) if r.get("status") == "pending"]
    
    total_users = len(users)
    blocked_count = len(blocked)
    
    stats_text = (
        f"📊 <b>Bot Statistics</b>\n\n"
        f"👤 Total Users: <b>{total_users}</b>\n"
        f"🚫 Blocked Users: <b>{blocked_count}</b>\n"
        f"💸 Pending Withdrawals: <b>{len(pending_withdrawals)}</b>"
    )
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Back to Admin Menu", callback_data="admin_main"))
    bot.edit_message_text(stats_text, chat_id, message_id, reply_markup=keyboard)


def list_tasks_for_admin(chat_id, message_id=None):
    bot_data = get_bot_data()
    tasks = bot_data.get("tasks", [])
    
    text = "📋 <b>Current Tasks:</b>\n\n"
    if not tasks:
        text += "No tasks found."
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for task in tasks:
        status_icon = "🟢" if task.get("active", False) else "🔴"
        text += f"{status_icon} <b>{task['title']}</b> (ID: <code>{task['id']}</code>)\n"                 f"Reward: ₹{task['reward']}, Done: {task.get('completed_count', 0)}/{task['quantity']}\n\n"
        
        toggle_text = "Deactivate" if task.get("active", False) else "Activate"
        keyboard.add(
            types.InlineKeyboardButton(f"{toggle_text} ({task['id']})", callback_data=f"admin_toggle_{task['id']}"),
            types.InlineKeyboardButton(f"🗑️ Delete ({task['id']})", callback_data=f"admin_delete_{task['id']}")
        )
    
    keyboard.add(types.InlineKeyboardButton("⬅️ Back", callback_data="admin_main"))
    
    try:
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, reply_markup=keyboard)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"Error editing message for list_tasks: {e}")
        if message_id: bot.send_message(chat_id, text, reply_markup=keyboard)


def start_add_task_wizard(message):
    msg = bot.send_message(message.chat.id, "✏️ *Step 1/5: Enter Task Title*\n\nExample: 'Download App'\nType /cancel to abort.")
    bot.register_next_step_handler(msg, process_task_title)

def process_task_title(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    task_data = {"title": message.text}
    msg = bot.send_message(message.chat.id, "📝 *Step 2/5: Enter Task Description*\n\nExample: 'Download this app and register.'")
    bot.register_next_step_handler(msg, process_task_description, task_data)

def process_task_description(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    task_data["description"] = message.text
    msg = bot.send_message(message.chat.id, "🌐 *Step 3/5: Enter Task Link*\n\nExample: 'https://play.google.com/store/apps/details?id=com.example.app'")
    bot.register_next_step_handler(msg, process_task_link, task_data)

def process_task_link(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    task_data["link"] = message.text
    msg = bot.send_message(message.chat.id, "💰 *Step 4/5: Enter Reward Amount (e.g., 5 or 2.5)*")
    bot.register_next_step_handler(msg, process_task_reward, task_data)

def process_task_reward(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    try:
        task_data["reward"] = float(message.text)
        msg = bot.send_message(message.chat.id, "🔢 *Step 5/5: Enter Quantity (total number of times this task can be completed)*")
        bot.register_next_step_handler(msg, process_task_quantity, task_data)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Invalid number. Please enter a valid reward amount.")
        bot.register_next_step_handler(msg, process_task_reward, task_data)

def process_task_quantity(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    try:
        task_data["quantity"] = int(message.text)
        
        # Finalize and save task
        bot_data = get_bot_data()
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "title": task_data["title"],
            "description": task_data["description"],
            "link": task_data["link"],
            "reward": task_data["reward"],
            "quantity": task_data["quantity"],
            "completed_count": 0,
            "active": True,
            "created_at": time.time()
        }
        bot_data.setdefault("tasks", []).append(new_task)
        save_bot_data(bot_data)
        
        bot.send_message(message.chat.id, f"✅ *Task Created Successfully!* \nID: <code>{new_task['id']}</code>")
        log_activity(ADMIN_ID, "admin_task_added", new_task)
        show_admin_menu(message.chat.id)

    except ValueError:
        msg = bot.send_message(message.chat.id, "Invalid number. Please enter a valid quantity.")
        bot.register_next_step_handler(msg, process_task_quantity, task_data)


def process_broadcast_message(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Broadcast cancelled.")
        show_admin_menu(message.chat.id)
        return

    users = load_json_file(USERS_DATA_FILE)
    user_ids = list(users.keys())
    sent_count = 0
    failed_count = 0
    
    bot.send_message(message.chat.id, f"Starting broadcast to {len(user_ids)} users. This may take a while...")
    
    for user_id in user_ids:
        try:
            bot.send_message(user_id, message.text)
            sent_count += 1
        except Exception:
            failed_count += 1
        time.sleep(0.1) # Avoid hitting API limits
        
    bot.send_message(message.chat.id, f"📢 *Broadcast Complete*\n\nSent: {sent_count}\nFailed: {failed_count}")
    show_admin_menu(message.chat.id)


def process_unblock_user(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Unblock operation cancelled.")
        show_admin_menu(message.chat.id)
        return
    
    try:
        user_id_to_unblock = int(message.text.strip())
        if unblock_user(user_id_to_unblock):
            bot.send_message(message.chat.id, f"✅ User <code>{user_id_to_unblock}</code> has been unblocked.")
        else:
            bot.send_message(message.chat.id, f"⚠️ User <code>{user_id_to_unblock}</code> was not found in the block list.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid User ID. Please provide a numeric ID.")
    
    show_admin_menu(message.chat.id)


# -----------------------------------------------------------------------------
# ------------------------- CALLBACK QUERY HANDLERS ---------------------------
# -----------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_', 'block_')))
def handle_verification_callbacks(call):
    if not is_admin(call.from_user.id): return
    action, data = call.data.split('_', 1)
    
    if action == "block":
        user_id = int(data)
        if block_user(user_id):
            bot.answer_callback_query(call.id, f"User {user_id} has been blocked.")
            bot.edit_message_caption(caption=call.message.caption + "\n\n🚫 User Blocked",
                                     chat_id=call.message.chat.id, message_id=call.message.message_id)
            try:
                bot.send_message(user_id, get_message(user_id, "user_blocked"))
            except Exception as e:
                print(f"Could not notify user {user_id} of blocking: {e}")
        else:
            bot.answer_callback_query(call.id, f"User {user_id} is already blocked.")
        return

    user_id, task_id, reward_str = data.split('_')
    user_id = int(user_id)
    reward = float(reward_str)
    
    user_data = get_user_data(user_id)
    if not user_data:
        bot.answer_callback_query(call.id, "Error: User data not found.")
        return
    
    if action == "approve":
        user_data["balance"] += reward
        user_data["total_earnings"] += reward
        user_data["completed_tasks"].append(task_id)
        user_data["current_task"] = None
        update_user_data(user_id, user_data)
        
        bot_data = get_bot_data()
        task = next((t for t in bot_data.get("tasks", []) if t["id"] == task_id), None)
        if task:
            task["completed_count"] = task.get("completed_count", 0) + 1
            save_bot_data(bot_data)

        bot.answer_callback_query(call.id, "Task Approved!")
        bot.edit_message_caption(caption=call.message.caption + f"\n\n✅ Approved by {call.from_user.first_name}",
                                 chat_id=call.message.chat.id, message_id=call.message.message_id)
        try:
            bot.send_message(user_id, get_message(user_id, "task_approved", reward=reward))
        except Exception as e:
            print(f"Could not notify user {user_id} of approval: {e}")
        log_activity(user_id, "task_approved", {"task_id": task_id, "reward": reward, "admin_id": call.from_user.id})

    elif action == "reject":
        user_data["balance"] -= REJECTION_PENALTY
        if user_data["balance"] < 0: user_data["balance"] = 0
        user_data["current_task"] = None
        update_user_data(user_id, user_data)
        
        bot.answer_callback_query(call.id, "Task Rejected!")
        bot.edit_message_caption(caption=call.message.caption + f"\n\n❌ Rejected by {call.from_user.first_name}",
                                 chat_id=call.message.chat.id, message_id=call.message.message_id)
        try:
            bot.send_message(user_id, get_message(user_id, "task_rejected", penalty=REJECTION_PENALTY))
        except Exception as e:
            print(f"Could not notify user {user_id} of rejection: {e}")
        log_activity(user_id, "task_rejected", {"task_id": task_id, "penalty": REJECTION_PENALTY, "admin_id": call.from_user.id})


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment_callbacks(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split('_')
    action, request_id = parts[1], parts[2]
    
    bot_data = get_bot_data()
    requests = bot_data.get("withdrawal_requests", [])
    request = next((r for r in requests if r["id"] == request_id), None)
    
    if not request or request.get("status") != "pending":
        bot.answer_callback_query(call.id, "Error: Request not found or already processed.")
        return
        
    if action == "approve":
        request["status"] = "approved"
        save_bot_data(bot_data)
        bot.answer_callback_query(call.id, "Payment Approved.")
        bot.edit_message_text(text=call.message.text + f"\n\n✅ Approved by {call.from_user.first_name}",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        try:
            bot.send_message(request["user_id"], f"🎉 Your withdrawal request for ₹{request['amount']:.2f} has been approved and processed.")
        except Exception as e:
            print(f"Could not notify user of payment approval: {e}")
        log_activity(request["user_id"], "withdrawal_approved", {"request_id": request_id, "admin_id": call.from_user.id})
    
    elif action == "reject":
        user_id, amount = int(parts[3]), float(parts[4])
        
        request["status"] = "rejected"
        save_bot_data(bot_data)
        
        user_data = get_user_data(user_id)
        if user_data:
            user_data["balance"] += amount
            update_user_data(user_id, user_data)
        
        bot.answer_callback_query(call.id, "Payment Rejected and Refunded.")
        bot.edit_message_text(text=call.message.text + f"\n\n❌ Rejected & Refunded by {call.from_user.first_name}",
                              chat_id=call.message.chat.id, message_id=call.message.message_id)
        try:
            bot.send_message(user_id, f"😔 Your withdrawal request for ₹{amount:.2f} was rejected. The amount has been refunded to your bot balance.")
        except Exception as e:
            print(f"Could not notify user of payment rejection: {e}")
        log_activity(user_id, "withdrawal_rejected", {"request_id": request_id, "admin_id": call.from_user.id})


@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def handle_language_selection(call):
    lang = call.data.split('_')[1]
    user_id = call.from_user.id
    user_data = get_user_data(user_id)
    if user_data:
        user_data["language"] = lang
        update_user_data(user_id, user_data)
        bot.answer_callback_query(call.id, f"Language set to {lang.capitalize()}")
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(user_id, get_message(user_id, "lang_changed"), reply_markup=get_main_menu_keyboard(user_id))
        log_activity(user_id, "language_change", {"language": lang})

# -----------------------------------------------------------------------------
# -------------------------- WEB SERVER FOR HEALTH CHECKS ---------------------
# -----------------------------------------------------------------------------
# This Flask app is now intended to be run by a production WSGI server like Gunicorn.
# It provides a simple health check endpoint that hosting services can use.
@app.route('/')
def home():
    html_page = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bot Status</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f0f2f5; color: #333; margin: 0; padding: 20px; text-align: center; }
            .container { background-color: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; }
            h1 { color: #4CAF50; }
            p { font-size: 1.2em; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Bot is Active!</h1>
            <p>Your Telegram Task Reward Bot is running smoothly.</p>
            <p><small>Bot Username: @""" + BOT_USERNAME + """</small></p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_page)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "bot_username": BOT_USERNAME})

# -----------------------------------------------------------------------------
# -------------------------- BOT POLLING FUNCTION -----------------------------
# -----------------------------------------------------------------------------
def run_bot_polling():
    """Contains the main polling loop with error handling."""
    print(f"Bot '{BOT_USERNAME}' is starting polling...")
    log_activity("SYSTEM", "bot_startup")
    
    while True:
        try:
            print("Attempting to delete webhook and clear updates...")
            bot.delete_webhook(drop_pending_updates=True)
            time.sleep(1)
            print("Starting bot polling...")
            # The 'none_stop=True' parameter keeps the bot running even if there are errors.
            bot.polling(none_stop=True, interval=2, timeout=30)
            # Polling is a blocking call, so the loop will stay here.
            # If it exits, it means there was a critical error.
            print("Bot polling has stopped unexpectedly. Restarting in 10 seconds...")
            time.sleep(10)
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}. Retrying in 15 seconds...")
            time.sleep(15)
        except telebot.apihelper.ApiTelegramException as e:
            if "Conflict" in e.description:
                print("Conflict error (409): Another instance might be running. Retrying after clearing updates...")
                time.sleep(20)
            else:
                print(f"Telegram API Error: {e}. Retrying in 20 seconds...")
                time.sleep(20)
        except Exception as e:
            print(f"An unexpected error occurred in polling loop: {e}. Restarting polling in 30 seconds...")
            log_activity("SYSTEM", "polling_error", {"error": str(e)})
            time.sleep(30)

# -----------------------------------------------------------------------------
# ----------------------------- MAIN EXECUTION --------------------------------
# -----------------------------------------------------------------------------
# This part of the script runs when the module is loaded by the WSGI server.
# It initializes data and starts the bot's polling loop in a background thread.

print("Initializing data files...")
initialize_data_files()

# Start the bot polling in a separate thread.
# The 'daemon=True' ensures the thread will exit when the main program exits.
polling_thread = threading.Thread(target=run_bot_polling, daemon=True)
polling_thread.start()
print("Bot polling thread has been started. The web server can now start.")

# The Flask 'app' object will be picked up by the Gunicorn server.
# To run this for development, use the command: gunicorn bot:app
# For deployment on services like Render, set the start command to 'gunicorn bot:app'
