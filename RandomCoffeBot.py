import telegram
from telegram.ext import Updater, PollAnswerHandler
import schedule
import time
import json
import random

# Configuration
TOKEN = 'your_bot_token'  # Replace with your bot token from BotFather
CHAT_ID = 'your_chat_id'  # Replace with your group chat ID

# Persistent storage files
POLL_ID_FILE = 'current_poll_id.json'
PARTICIPANTS_FILE = 'participants.json'

# Global variables
current_poll_id = None
participants = {}  # Dictionary: user_id -> first_name

# Load data from files on startup
def load_data():
    global current_poll_id, participants
    try:
        with open(POLL_ID_FILE, 'r') as f:
            current_poll_id = json.load(f)
    except FileNotFoundError:
        current_poll_id = None
    try:
        with open(PARTICIPANTS_FILE, 'r') as f:
            participants = json.load(f)
    except FileNotFoundError:
        participants = {}

# Save data to files
def save_data():
    with open(POLL_ID_FILE, 'w') as f:
        json.dump(current_poll_id, f)
    with open(PARTICIPANTS_FILE, 'w') as f:
        json.dump(participants, f)

# Send the weekly poll
def send_poll():
    global current_poll_id, participants
    participants.clear()  # Reset participants for the new week
    poll = bot.send_poll(
        chat_id=CHAT_ID,
        question="Do you want to participate in this week's random coffee call?",
        options=["Yes", "No"],
        is_anonymous=False,
        allows_multiple_answers=False
    )
    current_poll_id = poll.poll.id
    save_data()

# Pair up participants and announce in the chat
def pair_up():
    global current_poll_id, participants
    if current_poll_id is None:
        return
    # Stop the poll
    bot.stop_poll(chat_id=CHAT_ID, poll_id=current_poll_id)
    # Check if there are enough participants
    participant_ids = list(participants.keys())
    if len(participant_ids) < 2:
        bot.send_message(chat_id=CHAT_ID, text="Not enough participants this week.")
    else:
        # Shuffle and create pairs
        random.shuffle(participant_ids)
        pairs = []
        for i in range(0, len(participant_ids), 2):
            if i + 1 < len(participant_ids):
                pairs.append((participant_ids[i], participant_ids[i+1]))
            else:
                if pairs:  # If odd number, add to last pair
                    pairs[-1] = pairs[-1] + (participant_ids[i],)
        # Create announcement message
        message = "This week's random coffee pairs are:\n"
        for pair in pairs:
            mentions = [f"[{participants[user_id]}](tg://user?id={user_id})" for user_id in pair]
            if len(pair) == 2:
                message += f"- {mentions[0]} and {mentions[1]}\n"
            elif len(pair) == 3:
                message += f"- {mentions[0]}, {mentions[1]}, and {mentions[2]}\n"
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
    # Reset for next week
    current_poll_id = None
    participants.clear()
    save_data()

# Handle poll answers
def poll_answer_handler(update, context):
    global participants
    if update.poll_answer.poll_id == current_poll_id:
        user = update.poll_answer.user
        option = update.poll_answer.option_ids[0]  # 0 = "Yes", 1 = "No"
        if option == 0:  # User chose "Yes"
            participants[user.id] = user.first_name
        else:  # User chose "No" or changed vote
            participants.pop(user.id, None)
        save_data()

# Initialize bot
updater = Updater(TOKEN, use_context=True)
bot = updater.bot
dp = updater.dispatcher
dp.add_handler(PollAnswerHandler(poll_answer_handler))

# Load existing data
load_data()

# Schedule tasks (adjust times as needed)
schedule.every().monday.at("10:00").do(send_poll)
schedule.every().wednesday.at("10:00").do(pair_up)

# Start the bot
updater.start_polling()

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)
