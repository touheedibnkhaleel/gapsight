"""
Analyzer service — handles all LLM calls and gap analysis logic.
Completely separate from HTTP routing and scraping.
"""

import requests
import json
import time
from typing import List
from fastapi import HTTPException
from core.config import OPENROUTER_API_KEY, OPENROUTER_URL, FREE_MODELS


# ── Gap Analysis Instructions ──────────────────────────────────────────────────
# Exported here so they can be updated in one place
# without touching routes or scraper logic

SYSTEM_PROMPT = """You are a senior product strategist working with early-stage founders.
Your task is deep gap analysis — NOT summarization.
Read between the lines. Find what users are NOT clearly communicating.
Respond ONLY with a valid JSON object. No markdown. No explanation."""

ANALYSIS_INSTRUCTIONS = """Return a JSON object with EXACTLY these 4 keys:

"blind_spots": 3-5 features or areas users almost never mention.
Things invisible to them — either they don't know the feature exists
or have given up expecting it.

"weak_signals": 3-5 subtle frustrations buried in positive or neutral reviews.
Look for hedged language: "but", "although", "wish", "sometimes", "a bit".
These are cracks before the churn.

"opportunities": 3-5 unmet needs users hint at but never directly demand.
What workarounds do they describe? What would push them from satisfied to obsessed?

"strategic_insights": 3-5 specific, high-priority recommendations for the founder.
What to fix or build first based on the gap patterns found.

Rules:
- Be specific to THIS product and THESE reviews only
- No generic advice like "improve UX" or "add more features"
- Every item must reference something concrete from the reviews
- Return ONLY the raw JSON object"""


def call_llm(prompt: str, system: str) -> str:
    """
    Call OpenRouter API with automatic model fallback.
    Tries each free model in order until one works.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GapSight",
    }

    last_error = ""

    for model in FREE_MODELS:
        print(f"⏳ Trying model: {model}")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            "temperature": 0.4,
            "max_tokens": 1500,
        }

        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )

            if resp.status_code == 401:
                raise HTTPException(
                    401,
                    "Invalid OpenRouter API key. "
                    "Get a free key at https://openrouter.ai"
                )

            if resp.status_code == 429:
                secs = (
                    resp.json()
                    .get("error", {})
                    .get("metadata", {})
                    .get("retry_after_seconds", 30)
                )
                print(f"⚠️  {model} rate-limited ({secs}s) — trying next...")
                last_error = f"{model} rate-limited"
                time.sleep(1)
                continue

            if not resp.ok:
                msg = resp.json().get("error", {}).get("message", resp.text)
                print(f"❌ {model} error {resp.status_code}: {msg}")
                last_error = msg
                continue

            content = resp.json()["choices"][0]["message"]["content"].strip()
            print(f"✅ Success: {model}")
            return content

        except HTTPException:
            raise
        except requests.Timeout:
            print(f"⏱️  {model} timed out")
            last_error = "timeout"
            continue
        except Exception as e:
            print(f"❌ {model}: {e}")
            last_error = str(e)
            continue

    raise HTTPException(
        503,
        f"All models unavailable. Last error: {last_error}. "
        f"Wait 60 seconds and retry."
    )


def analyze_reviews(
    product_name: str,
    product_description: str,
    reviews: List[str]
) -> dict:
    """
    Run gap analysis on a list of reviews.
    Returns structured JSON with blind spots, weak signals,
    opportunities and strategic insights.
    """
    reviews_block = "\n\n".join(
        [f"Review {i+1}: {r}" for i, r in enumerate(reviews)]
    )

    prompt = f"""Product Name: {product_name}
Product Description: {product_description}

User Reviews ({len(reviews)} total):
{reviews_block}

{ANALYSIS_INSTRUCTIONS}"""

    raw = call_llm(prompt, SYSTEM_PROMPT)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
