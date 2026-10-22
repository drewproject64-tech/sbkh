# SB24GZ KH

A Khmer-interface English vocabulary Telegram bot with exactly three main menu buttons:

- **📚 ពាក្យប្រចាំថ្ងៃ** — five English words, Khmer meanings and English example sentences.
- **📝 សំណួរខ្លីៗ** — three-choice questions with immediate Khmer feedback.
- **📈 វឌ្ឍនភាពរបស់ខ្ញុំ** — lesson days, current reading streak, quiz answers and accuracy.

Includes 35 words across seven rotating lessons. Daily lessons change at midnight in Asia/Phnom_Penh and repeat weekly. Lessons are marked read when delivered, once per calendar day; they are not proof of mastery. Quizzes draw from all 35 words and start on demand, one question at a time. Starting another question invalidates the previous unanswered one. No scheduled messages or external destination links.

## Run

1. Create the Telegram bot through **@BotFather** with `/newbot`. Choose an available username ending in `bot`.
2. Install Python **3.12 or newer**. No third-party Python packages are required.
3. Set `BOT_TOKEN` in your hosting secret/environment settings. Never put the token in GitHub or send it in chat.
4. Set `DATABASE_PATH` to a writable persistent location (default: `data/sbkh.sqlite3`).
5. Start with `python bot.py`.

The `.env.example` documents the settings; the application does not automatically load `.env` files. Export the settings in your shell or configure them in the hosting dashboard.

At startup the bot sets its display name, about text, description and command menu to match the learning features. A profile picture must be uploaded separately in BotFather. The username is managed in BotFather, not by this code.

## Docker

Build: `docker build -t sbkh .`

Run after exporting BOT_TOKEN:

```sh
docker run --name sbkh --restart unless-stopped -e BOT_TOKEN -e DATABASE_PATH=/data/sbkh.sqlite3 -v sbkh-data:/data sbkh
```

Use an always-on worker/container with a persistent volume mounted at `/data`. Start only **one** instance for a token and database. This is a long-polling bot, not an HTTP web service. Do not enable multiple replicas. Stop the old process before starting its replacement. Existing webhooks are detected and require deliberate removal before polling starts. Conflict errors stop the application rather than silently fighting another poller.

## Commands and privacy

`/start`, `/menu`, `/help`, `/words`, `/quiz`, `/progress`, `/privacy`, `/delete_data`.

Only Telegram numeric IDs, lesson dates and quiz results are stored. No names, phone numbers or message text are stored. `/delete_data` immediately deletes the requesting user's progress and quizzes. Backups are the operator's responsibility; protect the database and apply a backup retention policy. Use private chats for learning.

## Verification

Run `python -m unittest -v`. Automated tests cover menu/fallback responses, daily lesson deduplication, streaks, persistent storage, correct/wrong answers, callback ownership, duplicate taps and data deletion. They use a fake Telegram API and require no token.

Before promoting the bot, deploy it and manually check `/start`, all three buttons, quiz answers, restart persistence and `/delete_data` from a normal Telegram account. Repository tests do not verify a live token or hosting. Ad approval is not guaranteed.

## Files

- `bot.py`: Telegram API client, polling, handlers and SQLite persistence.
- `content.py`: editable Khmer copy and vocabulary.
- `test_bot.py`: offline behavior tests.
- `Dockerfile`: container deployment.

The implementation follows the official [Telegram Bot API](https://core.telegram.org/bots/api).
