import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly point to .env file location
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

OPENROUTER_API_KEY = "".join(os.getenv("OPENROUTER_API_KEY", "").split())
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
SERPAPI_KEY        = "".join(os.getenv("SERPAPI_KEY", "").split())

FREE_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
    "arcee-ai/trinity-large-preview:free",
]
