import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# OpenRouter
OPENROUTER_API_KEY = "".join(os.getenv("OPENROUTER_API_KEY", "").split())
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

# SerpApi — fallback hardcoded for Render until env var is confirmed working
_serpapi_env = os.getenv("SERPAPI_KEY", "")
SERPAPI_KEY  = "".join(_serpapi_env.split()) if _serpapi_env else "2832e50a33d90d9b774d77ec13a6c1149ce6cc75bc08f64c080dd4aa8160036a"

FREE_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
    "arcee-ai/trinity-large-preview:free",
]
