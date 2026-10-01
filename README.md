# AI Morning Brief — Phase 2

## Architecture

Tavily (max 10 searches/day)
        ↓
Deduplication + history
        ↓
NVIDIA Nemotron 3.5 Lightning 30B A3B
        ↓
Telegram
        ↓
All active subscribers

Nemotron is called once per daily run.
Tavily is called at most 10 times per daily run.
Subscribers do not multiply retrieval or master summarization cost.

## Telegram user flow

1. User opens the bot.
2. User taps Start once.
3. User optionally uses /topics.
4. User receives the briefing automatically every morning.
5. /stop pauses delivery.
6. /start resumes delivery.

## Local setup

Create `.env` from `.env.example`.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## NVIDIA

Model:

`nvidia/nemotron-3.5-lightning-30b-a3b`

Endpoint:

`https://integrate.api.nvidia.com/v1/chat/completions`

## GitHub Actions

The workflow runs at approximately 7:00 AM IST.

Add these repository secrets:

- TAVILY_API_KEY
- NVIDIA_API_KEY
- TELEGRAM_BOT_TOKEN
- TELEGRAM_ADMIN_CHAT_ID
- NVIDIA_MODEL
- NVIDIA_BASE_URL

The repository should be private.

Do not commit `.env` or API tokens.

## Important Telegram limitation

Telegram requires a user to initiate contact with a bot before the bot can send that user private messages. Therefore each teammate must open the bot and tap Start once. After that, the daily workflow sends messages automatically.
