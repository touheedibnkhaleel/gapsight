"""
Core configuration — loads all environment variables from .env
Never hardcode secrets. Always use os.getenv() here.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API
OPENROUTER_API_KEY = "".join(os.getenv("OPENROUTER_API_KEY", "").split())
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

# SerpApi
SERPAPI_KEY = "".join(os.getenv("SERPAPI_KEY", "").split())

# Free models tried in order — if one fails, next is used automatically
FREE_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
    "arcee-ai/trinity-large-preview:free",
]
