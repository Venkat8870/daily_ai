import hashlib
import sqlite3
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests

from config import (
    TAVILY_API_KEY,
    NEWS_DOMAINS,
    SEARCHES,
    MAX_TAVILY_CALLS,
    MAX_RESULTS_PER_SEARCH,
    TAVILY_SEARCH_DEPTH,
    DATABASE_FILE,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)


def request_with_retry(method, url, **kwargs):
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method,
                url,
                timeout=REQUEST_TIMEOUT,
                **kwargs,
            )

            if response.status_code in {408, 429, 500, 502, 503, 504}:
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** (attempt - 1))
                    continue

            return response

        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(2 ** (attempt - 1))
            else:
                raise

    raise last_error or RuntimeError("HTTP request failed")


def initialize_database():
    with sqlite3.connect(DATABASE_FILE) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                url TEXT UNIQUE,
                title TEXT,
                source TEXT,
                topic TEXT,
                published_date TEXT,
                created_at TEXT
            )
        """)


def article_exists(url):
    with sqlite3.connect(DATABASE_FILE) as con:
        row = con.execute(
            "SELECT id FROM articles WHERE url = ?",
            (url,),
        ).fetchone()
        return row is not None


def save_article(article):
    article_id = hashlib.sha256(
        article["url"].encode("utf-8")
    ).hexdigest()

    with sqlite3.connect(DATABASE_FILE) as con:
        con.execute("""
            INSERT OR IGNORE INTO articles
            (id, url, title, source, topic, published_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            article["url"],
            article["title"],
            article["source"],
            article["topic"],
            article.get("published_date", ""),
            datetime.now(timezone.utc).isoformat(),
        ))


def extract_domain(url):
    try:
        host = urlparse(url).hostname or "Unknown"
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return "Unknown"


def normalize_url(url):
    return url.lower().strip().split("?")[0].rstrip("/")


def search_tavily(query):
    response = request_with_retry(
        "POST",
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "topic": "news",
            "time_range": "day",
            "search_depth": TAVILY_SEARCH_DEPTH,
            "max_results": MAX_RESULTS_PER_SEARCH,
            "include_answer": False,
            "include_raw_content": False,
            "include_domains": NEWS_DOMAINS,
        },
    )
    response.raise_for_status()
    return response.json()


def collect_news():
    articles = []
    calls = min(MAX_TAVILY_CALLS, len(SEARCHES))

    print(f"\n🔎 Tavily searches today: {calls}/{MAX_TAVILY_CALLS}")

    for index, query in enumerate(SEARCHES[:calls], start=1):
        print(f"[{index}/{calls}] {query}")

        try:
            data = search_tavily(query)

            for result in data.get("results", []):
                url = result.get("url")
                title = result.get("title", "")
                content = result.get("content", "")

                if not url or not title:
                    continue

                articles.append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "source": extract_domain(url),
                    "topic": query,
                    "published_date": result.get("published_date", ""),
                    "score": result.get("score", 0),
                })

        except Exception as exc:
            print(f"⚠️ Tavily search failed: {exc}")

    return articles


def deduplicate(articles):
    unique = {}

    for article in articles:
        key = normalize_url(article["url"])

        if key not in unique:
            unique[key] = article
        elif article["score"] > unique[key]["score"]:
            unique[key] = article

    return list(unique.values())


def remove_history(articles):
    return [
        article
        for article in articles
        if not article_exists(article["url"])
    ]


def rank(articles):
    return sorted(
        articles,
        key=lambda item: item.get("score", 0),
        reverse=True,
    )


def build_context(articles):
    blocks = []

    for i, article in enumerate(articles, start=1):
        blocks.append(f"""
ARTICLE {i}
TITLE: {article["title"]}
SOURCE: {article["source"]}
URL: {article["url"]}
PUBLISHED: {article.get("published_date", "")}
CONTENT: {article["content"][:3000]}
""")

    return "\n".join(blocks)
