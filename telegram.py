import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_API_BASE,
    TELEGRAM_ADMIN_CHAT_ID,
    SUBSCRIBERS_FILE,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    TOPICS,
)


def load_subscribers():
    path = Path(SUBSCRIBERS_FILE)

    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_subscribers(data):
    Path(SUBSCRIBERS_FILE).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def telegram_request(method, endpoint, **kwargs):
    url = f"{TELEGRAM_API_BASE}/{endpoint}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )

            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** (attempt - 1))
                    continue

            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                raise RuntimeError(str(data))

            return data

        except Exception:
            if attempt == MAX_RETRIES:
                raise
            time.sleep(2 ** (attempt - 1))


def split_message(text, limit=3900):
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""

    for paragraph in text.split("\n\n"):
        if len(current) + len(paragraph) + 2 <= limit:
            current = (
                paragraph
                if not current
                else current + "\n\n" + paragraph
            )
        else:
            if current:
                chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    # Safety for a single huge paragraph.
    final = []
    for chunk in chunks:
        while len(chunk) > limit:
            final.append(chunk[:limit])
            chunk = chunk[limit:]
        if chunk:
            final.append(chunk)

    return final


def send_message(chat_id, text):
    for chunk in split_message(text):
        telegram_request(
            "POST",
            "sendMessage",
            json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": False,
            },
        )


def send_admin_alert(text):
    if TELEGRAM_ADMIN_CHAT_ID:
        try:
            send_message(
                TELEGRAM_ADMIN_CHAT_ID,
                "🚨 AI Morning Brief\n\n" + text,
            )
        except Exception as exc:
            print(f"Admin alert failed: {exc}")


def topics_text():
    return "\n".join(
        f"{i}. {topic}"
        for i, topic in enumerate(TOPICS, start=1)
    )


def process_updates():
    """
    Users only need to interact once.
    After /start, they remain active until /stop.
    """
    subscribers = load_subscribers()
    updates = telegram_request(
        "GET",
        "getUpdates",
        params={
            "timeout": 5,
            "allowed_updates": json.dumps(["message"]),
        },
    ).get("result", [])

    if not updates:
        return

    for update in updates:
        message = update.get("message", {})
        chat = message.get("chat", {})
        chat_id = str(chat.get("id"))
        text = (message.get("text") or "").strip()

        if not chat_id:
            continue

        if text.startswith("/start"):
            subscribers[chat_id] = {
                "chat_id": chat_id,
                "name": chat.get("first_name", "there"),
                "username": chat.get("username", ""),
                "active": True,
                "topics": TOPICS.copy(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            save_subscribers(subscribers)

            send_message(
                chat_id,
                "👋 Welcome to AI Morning Brief!\n\n"
                "You're subscribed. From now on, your AI briefing "
                "will arrive automatically every morning.\n\n"
                "🎯 Use /topics to personalize what you receive.\n"
                "/status — view settings\n"
                "/stop — pause messages",
            )

        elif text.startswith("/stop"):
            if chat_id in subscribers:
                subscribers[chat_id]["active"] = False
                subscribers[chat_id]["updated_at"] = (
                    datetime.now(timezone.utc).isoformat()
                )
                save_subscribers(subscribers)

            send_message(
                chat_id,
                "⏸️ Daily briefing paused.\n"
                "Send /start to resume.",
            )

        elif text.startswith("/status"):
            user = subscribers.get(chat_id)

            if not user:
                send_message(chat_id, "Send /start to subscribe.")
                continue

            state = "ACTIVE ✅" if user["active"] else "PAUSED ⏸️"
            interests = "\n".join(
                f"• {x}" for x in user.get("topics", TOPICS)
            )

            send_message(
                chat_id,
                f"📊 Status: {state}\n\n"
                f"Your interests:\n{interests}",
            )

        elif text.startswith("/topics"):
            send_message(
                chat_id,
                "🎯 Choose interests.\n\n"
                f"{topics_text()}\n\n"
                "Reply with numbers, e.g.:\n"
                "2,5,6",
            )

        elif chat_id in subscribers and subscribers[chat_id]["active"]:
            parts = [
                x.strip()
                for x in text.replace(";", ",").split(",")
                if x.strip()
            ]

            selected = []

            for part in parts:
                if part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < len(TOPICS):
                        if TOPICS[idx] not in selected:
                            selected.append(TOPICS[idx])

            if selected:
                subscribers[chat_id]["topics"] = selected
                subscribers[chat_id]["updated_at"] = (
                    datetime.now(timezone.utc).isoformat()
                )
                save_subscribers(subscribers)

                send_message(
                    chat_id,
                    "✅ Interests saved!\n\n"
                    + "\n".join(f"• {x}" for x in selected)
                    + "\n\n"
                    "Your briefing will arrive automatically every morning.",
                )

        # Telegram update IDs are acknowledged after processing.
        update_id = update.get("update_id")
        if update_id is not None:
            telegram_request(
                "GET",
                "getUpdates",
                params={"offset": update_id + 1},
            )

    print(f"📱 Processed {len(updates)} Telegram update(s).")


def active_subscribers():
    return [
        user
        for user in load_subscribers().values()
        if user.get("active")
    ]
