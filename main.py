from datetime import datetime

from config import MAX_ARTICLES_FOR_LLM
from news import (
    initialize_database,
    collect_news,
    deduplicate,
    remove_history,
    rank,
    build_context,
    save_article,
)
from llm import generate_brief
from telegram import (
    process_updates,
    active_subscribers,
    send_message,
    send_admin_alert,
)


def main():
    initialize_database()
    print("\n==========================================")
    print("       🤖 AI MORNING BRIEF")
    print("==========================================")

    # 1. Process /start, /stop, /topics and /status.
    process_updates()

    subscribers = active_subscribers()

    print(f"👥 Active subscribers: {len(subscribers)}")

    # Don't spend Tavily/Nemotron credits when nobody subscribed.
    if not subscribers:
        print("No active subscribers. Nothing to send.")
        return

    # 2. Retrieve news — max 10 Tavily searches.
    articles = collect_news()
    print(f"📊 Retrieved: {len(articles)}")

    if not articles:
        raise RuntimeError("Tavily returned no articles.")

    # 3. Deduplicate and remove already-used articles.
    articles = deduplicate(articles)
    articles = remove_history(articles)
    articles = rank(articles)[:MAX_ARTICLES_FOR_LLM]

    print(f"🆕 Fresh articles sent to Nemotron: {len(articles)}")

    if not articles:
        print("No new articles today.")
        return

    # 4. ONE Nemotron call for the master briefing.
    context = build_context(articles)
    date_text = datetime.now().strftime("%A, %B %d, %Y")

    print("🧠 Calling NVIDIA Nemotron once...")
    briefing = generate_brief(context, date_text)

    print("\n" + briefing + "\n")

    # 5. Send the same verified master briefing to every subscriber.
    #    No additional LLM call per subscriber.
    successful = 0

    for user in subscribers:
        try:
            send_message(user["chat_id"], briefing)
            successful += 1
            print(f"✅ Sent to {user.get('name', user['chat_id'])}")
        except Exception as exc:
            print(f"❌ Failed for {user['chat_id']}: {exc}")

    # 6. Save history only after the pipeline successfully produced
    #    the briefing.
    for article in articles:
        save_article(article)

    print(
        f"\n✅ Complete: {successful}/{len(subscribers)} "
        "subscribers received the briefing."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n❌ PROGRAM FAILED: {type(exc).__name__}: {exc}")
        send_admin_alert(
            f"{type(exc).__name__}: {exc}"
        )
        raise
