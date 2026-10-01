import requests

from config import (
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MODEL,
    MAX_FINAL_STORIES,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
)


def generate_brief(context, date_text):
    prompt = f"""
Create a concise daily AI technology briefing for {date_text}.

Use ONLY the supplied retrieved articles.

Requirements:
- Select at most {MAX_FINAL_STORIES} important developments.
- Merge duplicate coverage of the same event.
- Do not invent facts.
- Do not claim something happened unless supported by the supplied text.
- Prefer primary-source reporting when available.
- Keep source URLs exactly as supplied.
- Explain why each development matters technically or commercially.
- Avoid hype.

Format:

🤖 AI MORNING BRIEF
📅 {date_text}

🔥 TOP AI DEVELOPMENTS

1️⃣ HEADLINE
What happened: 2-3 sentences.
Why it matters: 1-2 sentences.
🔗 Source: URL

...

🧠 MODELS & RESEARCH
• item

💰 AI BUSINESS
• item

🛠️ TOOLS & OPEN SOURCE
• item

🤖 ROBOTICS & HARDWARE
• item

⚡ 60-SECOND TAKEAWAY
• item
• item
• item

Keep the complete result below 3800 characters.

RETRIEVED ARTICLES:
{context}
"""

    url = f"{NVIDIA_BASE_URL.rstrip('/')}/chat/completions"

    payload = {
        "model": NVIDIA_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a rigorous AI news editor. "
                    "Use only evidence provided by the user."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature":1,
        "top_p": 0.95,
        "max_tokens": 1500,
    }

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {NVIDIA_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code in {429, 500, 502, 503, 504}:
                if attempt < MAX_RETRIES:
                    import time
                    time.sleep(2 ** (attempt - 1))
                    continue

            response.raise_for_status()
            data = response.json()

            text = data["choices"][0]["message"]["content"]

            if not text:
                raise RuntimeError("Nemotron returned empty content.")

            return text.strip()

        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        f"Nemotron failed after {MAX_RETRIES} attempts: {last_error}"
    )
