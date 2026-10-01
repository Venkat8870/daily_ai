import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

TOPICS = [
    "AI Models & Releases",
    "AI Agents",
    "AI Research",
]

NVIDIA_BASE_URL = os.getenv(
    "NVIDIA_BASE_URL",
    "https://integrate.api.nvidia.com/v1",
)
NVIDIA_MODEL = os.getenv(
    "NVIDIA_MODEL",
    "nvidia/nemotron-3.5-lightning-30b-a3b",
)

# Maximum Tavily searches per daily run.
MAX_TAVILY_CALLS = int(os.getenv("MAX_TAVILY_CALLS", "10"))
TAVILY_SEARCH_DEPTH = os.getenv("TAVILY_SEARCH_DEPTH", "basic")
MAX_RESULTS_PER_SEARCH = int(os.getenv("MAX_RESULTS_PER_SEARCH", "5"))

MAX_ARTICLES_FOR_LLM = int(os.getenv("MAX_ARTICLES_FOR_LLM", "5"))
MAX_FINAL_STORIES = int(os.getenv("MAX_FINAL_STORIES", "7"))

NEWS_DOMAINS = [
    "venturebeat.com",
    "techcrunch.com",
    "theverge.com",
    "arstechnica.com",
    "wired.com",
    "technologyreview.com",
    "openai.com",
    "anthropic.com",
    "blog.google",
    "deepmind.google",
    "nvidia.com",
    "microsoft.com",
    "ai.meta.com",
    "huggingface.co",
]

SEARCHES = [
    "latest AI model releases and major AI model updates",
    "latest AI agents agentic AI launches and developments",
    #"latest AI research breakthroughs papers and major research news",
    #"latest generative AI developments multimodal AI and foundation models",
    #"latest AI startups funding acquisitions partnerships and business",
    #"latest open source AI models releases and developer projects",
    #"latest AI developer tools APIs SDKs coding assistants and platforms",
    #"latest computer vision multimodal vision AI and video AI",
    #"latest robotics physical AI autonomous systems and humanoid robots",
    #"latest AI hardware GPUs chips inference accelerators and datacenter AI",
]

DATABASE_FILE = os.getenv("DATABASE_FILE", "news_history.db")
SUBSCRIBERS_FILE = os.getenv("SUBSCRIBERS_FILE", "subscribers.json")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "120"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))

# GitHub Actions schedule: 01:30 UTC = 07:00 IST.
DAILY_CRON = "30 1 * * *"
