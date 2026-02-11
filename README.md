# ITPM Club Random Coffee Bot

A Telegram bot that runs the ITPM community's weekly **Random Coffee** routine:

- sends a participation poll,
- collects opt-ins,
- randomly creates pairs (or one trio when needed),
- posts the weekly matching result in the group.

## Features

- Weekly poll scheduling (configurable day/time).
- Weekly automatic pairing schedule.
- Poll answers persisted on disk.
- Handles restarts without losing active poll context.
- Uses Telegram user mentions for easy introductions.

## Requirements

- Python 3.10+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A Telegram group chat ID

Install dependencies:

```bash
pip install python-telegram-bot==13.15 schedule
```

## Configuration

Set environment variables before running:

- `TELEGRAM_BOT_TOKEN` (required)
- `TELEGRAM_CHAT_ID` (required)
- `POLL_DAY` (optional, default: `monday`)
- `POLL_TIME` (optional, default: `10:00`)
- `PAIRING_DAY` (optional, default: `wednesday`)
- `PAIRING_TIME` (optional, default: `10:00`)
- `DATA_DIR` (optional, default: current directory)

Example:

```bash
export TELEGRAM_BOT_TOKEN="<your_token>"
export TELEGRAM_CHAT_ID="-1001234567890"
export POLL_DAY="monday"
export POLL_TIME="10:00"
export PAIRING_DAY="wednesday"
export PAIRING_TIME="10:00"
export DATA_DIR="./data"
```

## Run

```bash
python RandomCoffeBot.py
```

## Notes

- The bot uses the server's local timezone for scheduling.
- For odd participant counts, one trio is created.
- Keep the process running continuously (use systemd, Docker, or a process manager in production).
