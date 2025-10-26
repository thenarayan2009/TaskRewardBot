
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
# --------------------------- !! IMPORTANT !! ---------------------------------
# ----------------- CONFIGURE YOUR BOT AND ADMIN ID HERE ----------------------
# -----------------------------------------------------------------------------

# ❗️ STEP 1: Get your Bot Token from @BotFather on Telegram and paste it here.
BOT_TOKEN = "7635250199:AAFfFeZYdlhNjlgU3jGRwRdHF_ckRcRhPZk"  # <--- PASTE YOUR BOT TOKEN HERE

# ❗️ STEP 2: Get your numeric Telegram User ID from @userinfobot and paste it here.
ADMIN_ID = 5367009004  # <--- PASTE YOUR ADMIN ID HERE

# ❗️ STEP 3: Get your bot's username (without '@') from @BotFather.
BOT_USERNAME = "TaskRewardBot"  # <--- REPLACE WITH YOUR BOT's USERNAME

# -----------------------------------------------------------------------------
# --------------------------- CONFIGURATION VARIABLES -------------------------
# -----------------------------------------------------------------------------

# Penalty for rejected tasks
REJECTION_PENALTY = 1 # Amount in rupees

# Keep-alive server settings
FLASK_PORT = 5000
SELF_PING_URL = f"http://127.0.0.1:{FLASK_PORT}/ping"

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
app = Flask(__name__)

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
        "welcome_bonus_received": "🎁 आपको हमारे बॉट में शामिल होने के लिए <b>₹{bonus:.2f}</b> का स्वागत बोनस मिला है!",
        "new_task_notification": (
            "🎯 <b>नया कार्य उपलब्ध है!</b>\n\n"
            "<b>{title}</b>\n"
            "इनाम: ₹{reward}\n\n"
            "इसे प्राप्त करने के लिए '🎯 नया कार्य' बटन पर क्लिक करें!"
        ),
        "setting_update_notification": "⚙️ <b>बॉट अपडेट</b>: {setting_name} को बदलकर <b>{new_value}</b> कर दिया गया है।",
        "main_menu_buttons": ["🎯 नया कार्य", "💰 बैलेंस", "💸 निकासी", "🔗 रेफर", "❓ सहायता", "🌐 भाषा"],
        "setting_names": {
            "min_withdrawal": "न्यूनतम निकासी राशि",
            "welcome_bonus": "स्वागत बोनस",
            "referral_reward": "रेफरल इनाम",
            "referral_milestone_count": "रेफरल माइलस्टोन गिनती",
            "referral_milestone_reward": "रेफरल माइलस्टोन इनाम"
        }
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
        "welcome_bonus_received": "🎁 You have received a welcome bonus of <b>₹{bonus:.2f}</b> for joining our bot!",
        "new_task_notification": (
            "🎯 <b>New Task Available!</b>\n\n"
            "<b>{title}</b>\n"
            "Reward: ₹{reward}\n\n"
            "Click the '🎯 New Task' button to get it!"
        ),
        "setting_update_notification": "⚙️ <b>Bot Update</b>: The {setting_name} has been changed to <b>{new_value}</b>.",
        "main_menu_buttons": ["🎯 New Task", "💰 Balance", "💸 Withdraw", "🔗 Refer", "❓ Help", "🌐 Language"],
        "setting_names": {
            "min_withdrawal": "Minimum Withdrawal",
            "welcome_bonus": "Welcome Bonus",
            "referral_reward": "Referral Reward",
            "referral_milestone_count": "Referral Milestone Count",
            "referral_milestone_reward": "Referral Milestone Reward"
        }
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
                    "min_withdrawal": 10.0,
                    "referral_reward": 2.0,
                    "referral_milestone_count": 5,
                    "referral_milestone_reward": 10.0,
                    "welcome_bonus": 5.0,
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
    
    # Handle the special case for setting update notifications
    if key == "setting_update_notification":
        setting_name = kwargs.get(f"setting_name_{language}", kwargs.get("setting_name_english"))
        return MESSAGES[language][key].format(setting_name=setting_name, new_value=kwargs.get("new_value"))

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
# ------------------------ NOTIFICATION BROADCASTER -------------------------
# -----------------------------------------------------------------------------
def _broadcast_task(message_key, **kwargs):
    """The actual broadcasting task that runs in a thread."""
    users = load_json_file(USERS_DATA_FILE)
    for user_id_str in users.keys():
        try:
            user_id = int(user_id_str)
            if not is_user_blocked(user_id):
                notification_text = get_message(user_id, message_key, **kwargs)
                bot.send_message(user_id, notification_text)
                time.sleep(0.1) # To avoid hitting API rate limits
        except Exception as e:
            print(f"Failed to broadcast to user {user_id_str}: {e}")
    print(f"Broadcast for '{message_key}' completed.")

def broadcast_notification(message_key, **kwargs):
    """Starts a non-blocking broadcast to all users."""
    thread = threading.Thread(target=_broadcast_task, args=(message_key,), kwargs=kwargs, daemon=True)
    thread.start()

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
        bot_settings = get_bot_data()["settings"]
        welcome_bonus = bot_settings.get("welcome_bonus", 0.0)
        
        new_user = {
            "id": user_id,
            "first_name": user.first_name,
            "username": user.username,
            "balance": welcome_bonus,
            "total_earnings": welcome_bonus,
            "completed_tasks": [],
            "referrals": 0,
            "referred_by": None,
            "joined_at": time.time(),
            "current_task": None,
            "language": "hindi"
        }

        # Referral handling
        try:
            referrer_id = int(message.text.split(' ')[1])
            if str(referrer_id) != str(user_id) and get_user_data(referrer_id):
                new_user["referred_by"] = referrer_id
                
                # Update referrer data
                referrer_data = get_user_data(referrer_id)
                reward = bot_settings["referral_reward"]
                milestone_count = bot_settings["referral_milestone_count"]
                milestone_reward = bot_settings["referral_milestone_reward"]
                
                referrer_data["balance"] += reward
                referrer_data["total_earnings"] += reward
                referrer_data["referrals"] += 1
                
                # Check for milestone
                if referrer_data["referrals"] > 0 and referrer_data["referrals"] % milestone_count == 0:
                    referrer_data["balance"] += milestone_reward
                    referrer_data["total_earnings"] += milestone_reward
                    bot.send_message(referrer_id, get_message(referrer_id, "milestone_bonus", count=referrer_data["referrals"], bonus=milestone_reward))
                
                update_user_data(referrer_id, referrer_data)
                bot.send_message(referrer_id, get_message(referrer_id, "new_referral", reward=reward))
                log_activity(referrer_id, "referral_bonus", {"new_user_id": user_id, "reward": reward})
        except (IndexError, ValueError):
            referrer_id = None

        update_user_data(user_id, new_user)
        log_activity(user_id, "user_registered", {"referrer": referrer_id})

        # Send welcome bonus message
        if welcome_bonus > 0:
            bot.send_message(user_id, get_message(user_id, "welcome_bonus_received", bonus=welcome_bonus))
            log_activity(user_id, "welcome_bonus", {"amount": welcome_bonus})

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
    text = "🛠️ <b>Admin Panel</b>\n\nSelect an option:"
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("💸 Withdrawal Requests", callback_data="admin_withdrawals"),
        types.InlineKeyboardButton("🎯 Manage Tasks", callback_data="admin_list_tasks")
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 User Statistics", callback_data="admin_stats"),
        types.InlineKeyboardButton("💰 Adjust Balance", callback_data="admin_adjust_balance")
    )
    keyboard.add(
        types.InlineKeyboardButton("🚫 Block/Unblock User", callback_data="admin_block_menu"),
        types.InlineKeyboardButton("📢 Message Center", callback_data="admin_broadcast")
    )
    keyboard.add(
        types.InlineKeyboardButton("🔗 Referral Settings", callback_data="admin_ref_settings"),
        types.InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_bot_settings")
    )
    keyboard.add(
        types.InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
    )
    
    try:
        if message_id:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)
        else:
            bot.send_message(chat_id, text, reply_markup=keyboard)
    except Exception as e:
        if not message_id:
            print(f"Failed to send admin menu: {e}")

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

def list_tasks_for_admin(chat_id, message_id):
    bot_data = get_bot_data()
    tasks = bot_data.get("tasks", [])
    
    text = "🎯 <b>Manage Tasks:</b>\n\n"
    if not tasks:
        text += "No tasks found."
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for task in tasks:
        status_icon = "🟢" if task.get("active", False) else "🔴"
        text += f"{status_icon} <b>{task['title']}</b> (<code>{task['id']}</code>)\n" \
                f"   Reward: ₹{task['reward']}, Done: {task.get('completed_count', 0)}/{task['quantity']}\n"
        
        toggle_text = "Deactivate" if task.get("active", False) else "Activate"
        keyboard.add(
            types.InlineKeyboardButton(f"{toggle_text} ({task['id']})", callback_data=f"admin_toggle_{task['id']}"),
            types.InlineKeyboardButton(f"🗑️ Delete ({task['id']})", callback_data=f"admin_delete_{task['id']}")
        )
    
    keyboard.add(types.InlineKeyboardButton("➕ Add New Task", callback_data="admin_add_task"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Back", callback_data="admin_main"))
    
    bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)

def show_withdrawal_requests(chat_id, message_id):
    bot_data = get_bot_data()
    pending_requests = [r for r in bot_data.get("withdrawal_requests", []) if r.get("status") == "pending"]
    
    text = "💸 <b>Pending Withdrawal Requests</b>\n"
    keyboard = types.InlineKeyboardMarkup()

    if not pending_requests:
        text += "\nNo pending requests."
    else:
        for req in pending_requests:
            user_info = get_user_data(req['user_id'])
            user_name = user_info['first_name'] if user_info else 'Unknown'
            text += f"\n- - - - - - - - - - - - - -\n" \
                    f"<b>User:</b> {user_name} (<code>{req['user_id']}</code>)\n" \
                    f"<b>Amount:</b> ₹{req['amount']:.2f}\n" \
                    f"<b>UPI:</b> <code>{req['upi_id']}</code>\n"
            keyboard.row(
                types.InlineKeyboardButton(f"✅ Approve ({req['amount']:.0f})", callback_data=f"pay_approve_{req['id']}"),
                types.InlineKeyboardButton(f"❌ Reject", callback_data=f"pay_reject_{req['id']}_{req['user_id']}_{req['amount']}")
            )

    keyboard.add(types.InlineKeyboardButton("⬅️ Back", callback_data="admin_main"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)

def start_add_task_wizard(message):
    msg = bot.send_message(message.chat.id, "✏️ <b>Step 1/5: Enter Task Title</b>\n\nExample: 'Download App'\nType /cancel to abort.")
    bot.register_next_step_handler(msg, process_task_title)

def process_task_title(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    task_data = {"title": message.text}
    msg = bot.send_message(message.chat.id, "📝 <b>Step 2/5: Enter Task Description</b>\n\nExample: 'Download this app and register.'")
    bot.register_next_step_handler(msg, process_task_description, task_data)

def process_task_description(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    task_data["description"] = message.text
    msg = bot.send_message(message.chat.id, "🌐 <b>Step 3/5: Enter Task Link</b>\n\nExample: 'https://play.google.com/store/apps/details?id=com.example.app'")
    bot.register_next_step_handler(msg, process_task_link, task_data)

def process_task_link(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    task_data["link"] = message.text
    msg = bot.send_message(message.chat.id, "💰 <b>Step 4/5: Enter Reward Amount (e.g., 5 or 2.5)</b>")
    bot.register_next_step_handler(msg, process_task_reward, task_data)

def process_task_reward(message, task_data):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Task creation cancelled.")
        show_admin_menu(message.chat.id)
        return
    try:
        task_data["reward"] = float(message.text)
        msg = bot.send_message(message.chat.id, "🔢 <b>Step 5/5: Enter Quantity (total number of times this task can be completed)</b>")
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
        bot_data = get_bot_data()
        new_task = {
            "id": str(uuid.uuid4())[:8], "title": task_data["title"], "description": task_data["description"],
            "link": task_data["link"], "reward": task_data["reward"], "quantity": task_data["quantity"],
            "completed_count": 0, "active": True, "created_at": time.time()
        }
        bot_data.setdefault("tasks", []).append(new_task)
        save_bot_data(bot_data)
        bot.send_message(message.chat.id, f"✅ <b>Task Created Successfully!</b> \nID: <code>{new_task['id']}</code>")
        log_activity(ADMIN_ID, "admin_task_added", new_task)
        
        # Notify users about the new task
        broadcast_notification("new_task_notification", title=new_task['title'], reward=new_task['reward'])
        
        show_admin_menu(message.chat.id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Invalid number. Please enter a valid quantity.")
        bot.register_next_step_handler(msg, process_task_quantity, task_data)

def start_broadcast_wizard(message):
    msg = bot.send_message(message.chat.id, "📢 Please send the message you want to broadcast to all users. /cancel to abort.")
    bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Broadcast cancelled.")
        show_admin_menu(message.chat.id)
        return
    
    def broadcast_run(broadcast_text):
        users, sent_count, failed_count = load_json_file(USERS_DATA_FILE), 0, 0
        user_ids = list(users.keys())
        bot.send_message(message.chat.id, f"Starting broadcast to {len(user_ids)} users...")
        for user_id in user_ids:
            try:
                bot.send_message(user_id, broadcast_text)
                sent_count += 1
            except Exception:
                failed_count += 1
            time.sleep(0.1)
        bot.send_message(message.chat.id, f"📢 <b>Broadcast Complete</b>\n\nSent: {sent_count}\nFailed: {failed_count}")

    thread = threading.Thread(target=broadcast_run, args=(message.text,), daemon=True)
    thread.start()
    show_admin_menu(message.chat.id)

def show_block_unblock_menu(chat_id, message_id):
    text = "🚫 <b>Block/Unblock User</b>\n\nSelect an option:"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("🚫 Block User", callback_data="admin_block_user"),
        types.InlineKeyboardButton("🔓 Unblock User", callback_data="admin_unblock_user")
    )
    keyboard.add(types.InlineKeyboardButton("⬅️ Back", callback_data="admin_main"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)

def start_block_user_wizard(message):
    msg = bot.send_message(message.chat.id, "🚫 Please enter the User ID to block. /cancel to abort.")
    bot.register_next_step_handler(msg, process_block_user)

def process_block_user(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Block operation cancelled.")
        show_admin_menu(message.chat.id)
        return
    try:
        user_id_to_block = int(message.text.strip())
        if block_user(user_id_to_block):
            bot.send_message(message.chat.id, f"✅ User <code>{user_id_to_block}</code> has been blocked.")
            try: bot.send_message(user_id_to_block, get_message(user_id_to_block, "user_blocked"))
            except Exception: pass
        else:
            bot.send_message(message.chat.id, f"⚠️ User <code>{user_id_to_block}</code> is already blocked.")
    except ValueError:
        bot.send_message(message.chat.id, "Invalid User ID.")
    show_admin_menu(message.chat.id)

def start_unblock_user_wizard(message):
    msg = bot.send_message(message.chat.id, "🔓 Please enter the User ID to unblock. /cancel to abort.")
    bot.register_next_step_handler(msg, process_unblock_user)

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
        bot.send_message(message.chat.id, "Invalid User ID.")
    show_admin_menu(message.chat.id)

def start_adjust_balance_wizard(message):
    msg = bot.send_message(message.chat.id, "💰 <b>Adjust Balance</b>\nPlease enter the User ID. /cancel to abort.")
    bot.register_next_step_handler(msg, process_adjust_balance_id)

def process_adjust_balance_id(message):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Operation cancelled."); show_admin_menu(message.chat.id); return
    try:
        user_id = int(message.text)
        user_data = get_user_data(user_id)
        if not user_data:
            bot.send_message(message.chat.id, f"⚠️ User <code>{user_id}</code> not found. Try again."); start_adjust_balance_wizard(message); return
        msg = bot.send_message(message.chat.id, f"User: {user_data.get('first_name', 'N/A')} (<code>{user_id}</code>)\nCurrent Balance: ₹{user_data.get('balance', 0):.2f}\nEnter amount to add (use a negative number to subtract, e.g., -5).")
        bot.register_next_step_handler(msg, process_adjust_balance_amount, user_id)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid ID."); start_adjust_balance_wizard(message)

def process_adjust_balance_amount(message, user_id):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Operation cancelled."); show_admin_menu(message.chat.id); return
    try:
        amount = float(message.text)
        user_data = get_user_data(user_id)
        original_balance = user_data["balance"]
        user_data["balance"] += amount
        if user_data["balance"] < 0: user_data["balance"] = 0
        if amount > 0: user_data["total_earnings"] += amount
        update_user_data(user_id, user_data)
        bot.send_message(message.chat.id, f"✅ Balance updated for <code>{user_id}</code>.\nOld: ₹{original_balance:.2f} | New: ₹{user_data['balance']:.2f}")
        log_activity(ADMIN_ID, "admin_adjust_balance", {"target_user_id": user_id, "amount": amount})
        try: bot.send_message(user_id, f"💰 Admin adjusted your balance by ₹{amount:.2f}. New balance: ₹{user_data['balance']:.2f}.")
        except Exception: pass
        show_admin_menu(message.chat.id)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Invalid amount. Enter a number.")
        bot.register_next_step_handler(msg, process_adjust_balance_amount, user_id)

def show_bot_settings(chat_id, message_id):
    settings = get_bot_data().get("settings", {})
    text = (f"⚙️ <b>Bot Settings</b>\n\nCurrent Values:\n"
            f" • Minimum Withdrawal: <b>₹{settings.get('min_withdrawal', 0)}</b>\n"
            f" • Welcome Bonus: <b>₹{settings.get('welcome_bonus', 0)}</b>")
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("Change Min Withdrawal", callback_data="admin_change_setting_min_withdrawal"))
    keyboard.add(types.InlineKeyboardButton("Change Welcome Bonus", callback_data="admin_change_setting_welcome_bonus"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Back", callback_data="admin_main"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)

def show_referral_settings(chat_id, message_id):
    s = get_bot_data().get("settings", {})
    text = (f"🔗 <b>Referral Settings</b>\n\nCurrent Values:\n"
            f" • Reward per Referral: <b>₹{s.get('referral_reward', 0)}</b>\n"
            f" • Milestone Count: <b>{s.get('referral_milestone_count', 0)} referrals</b>\n"
            f" • Milestone Reward: <b>₹{s.get('referral_milestone_reward', 0)}</b>")
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(types.InlineKeyboardButton("Change Referral Reward", callback_data="admin_change_setting_referral_reward"))
    keyboard.add(types.InlineKeyboardButton("Change Milestone Count", callback_data="admin_change_setting_referral_milestone_count"))
    keyboard.add(types.InlineKeyboardButton("Change Milestone Reward", callback_data="admin_change_setting_referral_milestone_reward"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Back", callback_data="admin_main"))
    bot.edit_message_text(text, chat_id, message_id, reply_markup=keyboard)

def prompt_change_setting(message, setting_key, prompt_text, is_float=False):
    msg = bot.send_message(message.chat.id, prompt_text + "\nType /cancel to abort.")
    bot.register_next_step_handler(msg, process_setting_change, setting_key, is_float)

def process_setting_change(message, setting_key, is_float):
    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Operation cancelled."); show_admin_menu(message.chat.id); return
    try:
        new_value = float(message.text) if is_float else int(message.text)
        bot_data = get_bot_data()
        bot_data["settings"][setting_key] = new_value
        save_bot_data(bot_data)
        bot.send_message(message.chat.id, f"✅ Setting '<code>{setting_key}</code>' updated to <b>{new_value}</b>.")
        log_activity(ADMIN_ID, "admin_setting_change", {"setting": setting_key, "new_value": new_value})

        # Notify users of the change
        setting_name_hindi = MESSAGES["hindi"]["setting_names"].get(setting_key, setting_key)
        setting_name_english = MESSAGES["english"]["setting_names"].get(setting_key, setting_key)
        
        # Format the value correctly for the message
        display_value = f"₹{new_value:.2f}" if is_float else new_value
        
        broadcast_notification(
            "setting_update_notification",
            setting_name_hindi=setting_name_hindi,
            setting_name_english=setting_name_english,
            new_value=display_value
        )
        
        show_admin_menu(message.chat.id)
    except ValueError:
        bot.send_message(message.chat.id, "Invalid value. Please enter a valid number.")
        if "referral" in setting_key:
            show_referral_settings(message.chat.id, None) # Can't use message_id as it was deleted
        else:
            show_bot_settings(message.chat.id, None)

# --- Admin Callback Handler ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def handle_admin_callbacks(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "🚫 Unauthorized"); return

    action = call.data
    chat_id, message_id = call.message.chat.id, call.message.message_id
    
    # Menu Navigation
    menu_map = {
        "admin_main": show_admin_menu, "admin_refresh": show_admin_menu,
        "admin_stats": show_bot_stats, "admin_list_tasks": list_tasks_for_admin,
        "admin_withdrawals": show_withdrawal_requests, "admin_block_menu": show_block_unblock_menu,
        "admin_ref_settings": show_referral_settings, "admin_bot_settings": show_bot_settings
    }
    if action in menu_map:
        try: menu_map[action](chat_id, message_id)
        except telebot.apihelper.ApiTelegramException as e:
            if 'message is not modified' not in str(e): raise
        bot.answer_callback_query(call.id)
        return

    # Wizard Starters (deletes the menu)
    wizard_map = {
        "admin_add_task": start_add_task_wizard, "admin_broadcast": start_broadcast_wizard,
        "admin_adjust_balance": start_adjust_balance_wizard, "admin_block_user": start_block_user_wizard,
        "admin_unblock_user": start_unblock_user_wizard
    }
    if action in wizard_map:
        bot.delete_message(chat_id, message_id)
        wizard_map[action](call.message)
        bot.answer_callback_query(call.id)
        return
    
    # Settings Changers (deletes the menu)
    if action.startswith("admin_change_setting_"):
        setting_key = action.replace("admin_change_setting_", "")
        bot.delete_message(chat_id, message_id)
        prompts = {
            "min_withdrawal": ("Enter new minimum withdrawal amount.", True),
            "welcome_bonus": ("Enter new welcome bonus amount.", True),
            "referral_reward": ("Enter new reward per referral.", True),
            "referral_milestone_count": ("Enter new milestone count (e.g., 5).", False),
            "referral_milestone_reward": ("Enter new milestone reward amount.", True)
        }
        if setting_key in prompts:
            prompt_change_setting(call.message, setting_key, *prompts[setting_key])
        bot.answer_callback_query(call.id)
        return

    # Task List Actions (edits the list)
    if action.startswith(("admin_toggle_", "admin_delete_")):
        parts = action.split('_'); sub_action, task_id = parts[1], parts[2]
        bot_data = get_bot_data(); tasks = bot_data.get("tasks", [])
        if sub_action == "toggle":
            task = next((t for t in tasks if t["id"] == task_id), None)
            if task: task["active"] = not task.get("active", False)
        elif sub_action == "delete":
            bot_data["tasks"] = [t for t in tasks if t["id"] != task_id]
        save_bot_data(bot_data)
        list_tasks_for_admin(chat_id, message_id)
        bot.answer_callback_query(call.id)
        return
        
    bot.answer_callback_query(call.id)


# -----------------------------------------------------------------------------
# ------------------------- OTHER CALLBACK HANDLERS ---------------------------
# -----------------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: call.data.startswith(('approve_', 'reject_', 'block_')))
def handle_verification_callbacks(call):
    if not is_admin(call.from_user.id): return
    action, data = call.data.split('_', 1)
    
    if action == "block":
        user_id = int(data)
        if block_user(user_id):
            bot.answer_callback_query(call.id, f"User {user_id} blocked.")
            bot.edit_message_caption(caption=call.message.caption + "\n\n🚫 User Blocked",
                                     chat_id=call.message.chat.id, message_id=call.message.message_id)
            try: bot.send_message(user_id, get_message(user_id, "user_blocked"))
            except Exception as e: print(f"Could not notify user {user_id} of blocking: {e}")
        else:
            bot.answer_callback_query(call.id, f"User {user_id} is already blocked.")
        return

    user_id, task_id, reward = int(data.split('_')[0]), data.split('_')[1], float(data.split('_')[2])
    user_data = get_user_data(user_id)
    if not user_data: bot.answer_callback_query(call.id, "Error: User data not found."); return
    
    if action == "approve":
        user_data["balance"] += reward; user_data["total_earnings"] += reward
        user_data["completed_tasks"].append(task_id); user_data["current_task"] = None
        update_user_data(user_id, user_data)
        bot_data = get_bot_data()
        task = next((t for t in bot_data.get("tasks", []) if t["id"] == task_id), None)
        if task: task["completed_count"] = task.get("completed_count", 0) + 1; save_bot_data(bot_data)
        bot.answer_callback_query(call.id, "Task Approved!")
        bot.edit_message_caption(caption=call.message.caption + f"\n\n✅ Approved by {call.from_user.first_name}",
                                 chat_id=call.message.chat.id, message_id=call.message.message_id)
        try: bot.send_message(user_id, get_message(user_id, "task_approved", reward=reward))
        except Exception as e: print(f"Could not notify user {user_id} of approval: {e}")
        log_activity(user_id, "task_approved", {"task_id": task_id, "reward": reward, "admin_id": call.from_user.id})

    elif action == "reject":
        user_data["balance"] -= REJECTION_PENALTY
        if user_data["balance"] < 0: user_data["balance"] = 0
        user_data["current_task"] = None; update_user_data(user_id, user_data)
        bot.answer_callback_query(call.id, "Task Rejected!")
        bot.edit_message_caption(caption=call.message.caption + f"\n\n❌ Rejected by {call.from_user.first_name}",
                                 chat_id=call.message.chat.id, message_id=call.message.message_id)
        try: bot.send_message(user_id, get_message(user_id, "task_rejected", penalty=REJECTION_PENALTY))
        except Exception as e: print(f"Could not notify user {user_id} of rejection: {e}")
        log_activity(user_id, "task_rejected", {"task_id": task_id, "penalty": REJECTION_PENALTY, "admin_id": call.from_user.id})


@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def handle_payment_callbacks(call):
    if not is_admin(call.from_user.id): return
    parts = call.data.split('_'); action, request_id = parts[1], parts[2]
    bot_data = get_bot_data(); requests = bot_data.get("withdrawal_requests", [])
    request_index, request = next(((i, r) for i, r in enumerate(requests) if r["id"] == request_id), (None, None))
    
    if not request or request.get("status") != "pending":
        bot.answer_callback_query(call.id, "Error: Request not found or already processed.")
        try: show_withdrawal_requests(call.message.chat.id, call.message.message_id)
        except: pass # It might fail if no more requests are left
        return
        
    if action == "approve":
        request["status"] = "approved"
        log_activity(request["user_id"], "withdrawal_approved", {"request_id": request_id, "admin_id": call.from_user.id})
        bot.answer_callback_query(call.id, "Payment Approved.")
        try: bot.send_message(request["user_id"], f"🎉 Your withdrawal request for ₹{request['amount']:.2f} has been approved.")
        except Exception as e: print(f"Could not notify user of payment approval: {e}")
    
    elif action == "reject":
        user_id, amount = int(parts[3]), float(parts[4])
        request["status"] = "rejected"
        user_data = get_user_data(user_id)
        if user_data: user_data["balance"] += amount; update_user_data(user_id, user_data)
        log_activity(user_id, "withdrawal_rejected", {"request_id": request_id, "admin_id": call.from_user.id})
        bot.answer_callback_query(call.id, "Payment Rejected and Refunded.")
        try: bot.send_message(user_id, f"😔 Your withdrawal request for ₹{amount:.2f} was rejected. Amount refunded to balance.")
        except Exception as e: print(f"Could not notify user of payment rejection: {e}")
    
    # Update the request list in bot_data
    bot_data["withdrawal_requests"][request_index] = request
    save_bot_data(bot_data)
    
    # After action, refresh the withdrawal list
    try: 
        show_withdrawal_requests(call.message.chat.id, call.message.message_id)
    except telebot.apihelper.ApiTelegramException as e:
        if 'message is not modified' not in str(e):
            bot.delete_message(call.message.chat.id, call.message.message_id)
            show_withdrawal_requests(call.message.chat.id, None)


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
# -------------------------- KEEP-ALIVE WEB SERVER ----------------------------
# -----------------------------------------------------------------------------
@app.route('/')
def home():
    html_page = """
    <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Bot Status</title><style>body { font-family: Arial, sans-serif; background-color: #f0f2f5; color: #333; margin: 0; padding: 20px; text-align: center; } .container { background-color: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; } h1 { color: #4CAF50; } p { font-size: 1.2em; }</style></head><body><div class="container"><h1>✅ Bot is Active!</h1><p>Your Telegram Task Reward Bot is running smoothly.</p><p><small>Bot Username: @""" + BOT_USERNAME + """</small></p></div></body></html>
    """
    return render_template_string(html_page)

@app.route('/ping')
def ping(): return "Bot is alive!"

@app.route('/health')
def health(): return jsonify({"status": "ok", "bot_username": BOT_USERNAME})

def run_server(): app.run(host='0.0.0.0', port=FLASK_PORT)

def keep_alive():
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print(f"Keep-alive server started on port {FLASK_PORT}")

def self_ping_loop():
    while True:
        try: requests.get(SELF_PING_URL)
        except requests.exceptions.RequestException as e: print(f"Self-ping failed: {e}")
        time.sleep(120)

def heartbeat_loop():
    while True:
        print(f"Heartbeat: Bot is running... ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        time.sleep(240)

# -----------------------------------------------------------------------------
# ----------------------------- MAIN EXECUTION --------------------------------
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("Initializing data files...")
    initialize_data_files()
    
    print("Starting keep-alive server...")
    keep_alive()
    time.sleep(2)
    
    print("Starting background threads...")
    threading.Thread(target=self_ping_loop, daemon=True).start()
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    
    print(f"Bot '{BOT_USERNAME}' is starting...")
    log_activity("SYSTEM", "bot_startup")
    
    while True:
        try:
            bot.delete_webhook(drop_pending_updates=True)
            print("Starting bot polling...")
            bot.polling(none_stop=True, interval=2, timeout=30)
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}. Retrying in 15s...")
            time.sleep(15)
        except telebot.apihelper.ApiTelegramException as e:
            if e.error_code == 409: # Conflict error
                print("Conflict error (409) detected. Another instance might be running. Clearing webhook and retrying...")
                time.sleep(5)
            else:
                print(f"Telegram API Error: {e}. Retrying in 20s...")
                time.sleep(20)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Restarting polling in 30s...")
            log_activity("SYSTEM", "polling_error", {"error": str(e)})
            time.sleep(30)
