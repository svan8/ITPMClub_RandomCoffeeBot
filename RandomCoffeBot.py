import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Callable

import schedule
from telegram import Bot, ParseMode
from telegram.ext import PollAnswerHandler, Updater

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
POLL_DAY = os.getenv("POLL_DAY", "monday").lower()
POLL_TIME = os.getenv("POLL_TIME", "10:00")
PAIRING_DAY = os.getenv("PAIRING_DAY", "wednesday").lower()
PAIRING_TIME = os.getenv("PAIRING_TIME", "10:00")
DATA_DIR = Path(os.getenv("DATA_DIR", "."))

POLL_ID_FILE = DATA_DIR / "current_poll_id.json"
PARTICIPANTS_FILE = DATA_DIR / "participants.json"

current_poll_id = None
current_poll_message_id = None
participants = {}

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def validate_configuration() -> None:
    if not TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    if not CHAT_ID:
        raise ValueError("TELEGRAM_CHAT_ID environment variable is required")
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> None:
    global current_poll_id, current_poll_message_id, participants

    if POLL_ID_FILE.exists():
        with POLL_ID_FILE.open("r", encoding="utf-8") as file:
            poll_data = json.load(file)
            current_poll_id = poll_data.get("poll_id")
            current_poll_message_id = poll_data.get("message_id")
    else:
        current_poll_id = None
        current_poll_message_id = None

    if PARTICIPANTS_FILE.exists():
        with PARTICIPANTS_FILE.open("r", encoding="utf-8") as file:
            raw_participants = json.load(file)
            participants = {int(user_id): first_name for user_id, first_name in raw_participants.items()}
    else:
        participants = {}


def save_data() -> None:
    with POLL_ID_FILE.open("w", encoding="utf-8") as file:
        json.dump({"poll_id": current_poll_id, "message_id": current_poll_message_id}, file)

    serializable_participants = {str(user_id): first_name for user_id, first_name in participants.items()}
    with PARTICIPANTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(serializable_participants, file)


def send_poll(bot: Bot) -> None:
    global current_poll_id, current_poll_message_id, participants

    logger.info("Sending weekly poll to chat %s", CHAT_ID)
    participants.clear()

    poll_message = bot.send_poll(
        chat_id=CHAT_ID,
        question="Do you want to participate in this week's random coffee call?",
        options=["Yes", "No"],
        is_anonymous=False,
        allows_multiple_answers=False,
    )
    current_poll_id = poll_message.poll.id
    current_poll_message_id = poll_message.message_id
    save_data()


def build_pairs() -> list[tuple[int, ...]]:
    participant_ids = list(participants.keys())
    random.shuffle(participant_ids)

    pairs: list[tuple[int, ...]] = []
    for index in range(0, len(participant_ids), 2):
        if index + 1 < len(participant_ids):
            pairs.append((participant_ids[index], participant_ids[index + 1]))
        elif pairs:
            pairs[-1] = (*pairs[-1], participant_ids[index])
        else:
            pairs.append((participant_ids[index],))
    return pairs


def pair_up(bot: Bot) -> None:
    global current_poll_id, current_poll_message_id, participants

    if current_poll_id is None or current_poll_message_id is None:
        logger.info("No active poll found, skipping pair-up.")
        return

    logger.info("Closing poll and generating pairings.")
    bot.stop_poll(chat_id=CHAT_ID, message_id=current_poll_message_id)

    if len(participants) < 2:
        bot.send_message(chat_id=CHAT_ID, text="Not enough participants this week.")
    else:
        pairs = build_pairs()
        message_lines = ["This week's random coffee pairs are:"]
        for pair in pairs:
            mentions = [f"[{participants[user_id]}](tg://user?id={user_id})" for user_id in pair]
            if len(pair) == 2:
                message_lines.append(f"- {mentions[0]} and {mentions[1]}")
            elif len(pair) == 3:
                message_lines.append(f"- {mentions[0]}, {mentions[1]}, and {mentions[2]}")
            else:
                message_lines.append(f"- {mentions[0]}")

        bot.send_message(
            chat_id=CHAT_ID,
            text="\n".join(message_lines),
            parse_mode=ParseMode.MARKDOWN,
        )

    current_poll_id = None
    current_poll_message_id = None
    participants.clear()
    save_data()


def poll_answer_handler(update, _context) -> None:
    global participants

    if update.poll_answer.poll_id != current_poll_id:
        return

    user = update.poll_answer.user
    option = update.poll_answer.option_ids[0] if update.poll_answer.option_ids else 1

    if option == 0:
        participants[user.id] = user.first_name
    else:
        participants.pop(user.id, None)

    save_data()


def run_scheduled_job(job_name: str, job: Callable[[], None]) -> None:
    logger.info("Running scheduled %s at %s", job_name, datetime.now().astimezone().isoformat(timespec="seconds"))
    try:
        job()
    except Exception:
        logger.exception("Scheduled %s failed", job_name)


def schedule_job(day: str, execution_time: str, job: Callable[[], None], job_name: str) -> schedule.Job:
    day_method = getattr(schedule.every(), day, None)
    if day_method is None:
        raise ValueError(f"Unsupported day: {day}")

    scheduled_job = day_method.at(execution_time).do(lambda: run_scheduled_job(job_name, job))
    logger.info("Scheduled %s on %s at %s (next run: %s)", job_name, day, execution_time, scheduled_job.next_run)
    return scheduled_job


def main() -> None:
    validate_configuration()

    updater = Updater(TOKEN, use_context=True)
    bot = updater.bot
    dispatcher = updater.dispatcher
    dispatcher.add_handler(PollAnswerHandler(poll_answer_handler))

    load_data()

    poll_job = schedule_job(POLL_DAY, POLL_TIME, lambda: send_poll(bot), "poll")
    pairing_job = schedule_job(PAIRING_DAY, PAIRING_TIME, lambda: pair_up(bot), "pairing")

    updater.start_polling()
    logger.info(
        "Local scheduler time now %s (tzname=%s, poll next=%s, pairing next=%s)",
        datetime.now().astimezone().isoformat(timespec="seconds"),
        "/".join(time.tzname),
        poll_job.next_run,
        pairing_job.next_run,
    )
    logger.info("Bot started successfully.")

    last_heartbeat_minute = -1
    while True:
        schedule.run_pending()
        now = datetime.now()
        if now.minute != last_heartbeat_minute and now.minute % 15 == 0:
            logger.info("Scheduler heartbeat at %s", now.astimezone().isoformat(timespec="seconds"))
            last_heartbeat_minute = now.minute
        time.sleep(1)


if __name__ == "__main__":
    main()
