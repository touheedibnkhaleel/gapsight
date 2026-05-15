"""
GapSight — Review Gap Analyzer v3.1
=====================================
Paste a Product Hunt or Trustpilot URL → auto-scrape → gap analysis.

Powered by: OpenRouter (FREE, works from Pakistan, no region restrictions)
Get your free key at: https://openrouter.ai → Keys → Create Key

Set it in your terminal:
  export OPENROUTER_API_KEY="sk-or-v1-..."
Or hardcode it below for testing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json
import os
import time

# ─────────────────────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="GapSight API",
    description="Paste a product URL. Get gap insights automatically.",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gapsight-orpin.vercel.app",
        "http://localhost:3000",
        "*"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# OpenRouter Config
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()   # reads .env file automatically
# Paste your key here directly (get one free at https://openrouter.ai)
_raw_key = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_KEY = "".join(_raw_key.split())
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

# List of free models — tried in order until one works
# If one is rate-limited, it automatically tries the next one
FREE_MODELS = [
    "openrouter/auto",                              # OpenRouter auto-picks best available free model
    "meta-llama/llama-3.3-70b-instruct:free",       # LLaMA 3.3 70B
    "mistralai/mistral-small-3.1-24b-instruct:free",# Mistral Small 3.1
    "google/gemma-3-27b-it:free",                   # Gemma 3 27B
    "arcee-ai/trinity-large-preview:free",          # Trinity Large
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free", # Dolphin Mistral
]


def call_llm(prompt: str, system: str) -> str:
    """
    Call OpenRouter. Tries each free model in order.
    If one is rate-limited or unavailable, moves to the next automatically.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GapSight Review Analyzer",
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
            # response_format removed: not supported by all free models
        }

        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )

            # ── 401 Unauthorized — key is wrong ──
            if resp.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail=(
                        "OpenRouter API key is invalid. "
                        "Get a free key at https://openrouter.ai → Keys → Create Key. "
                        "Then set: OPENROUTER_API_KEY = 'sk-or-v1-...' in main.py"
                    )
                )

            # ── 429 Rate limited — try next model ──
            if resp.status_code == 429:
                retry_after = resp.json().get("error", {}).get("metadata", {}).get("retry_after_seconds", 30)
                print(f"⚠️  {model} is rate-limited (retry in {retry_after}s) — trying next model...")
                last_error = f"{model} rate-limited"
                time.sleep(1)   # Small pause before trying next model
                continue

            # ── Other HTTP error ──
            if not resp.ok:
                error_msg = resp.json().get("error", {}).get("message", resp.text)
                print(f"❌ {model} returned error {resp.status_code}: {error_msg}")
                last_error = error_msg
                continue

            # ── Success ──
            data    = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Success with model: {model}")
            return content

        except HTTPException:
            raise   # Re-raise auth errors immediately, don't retry

        except requests.Timeout:
            print(f"⏱️  {model} timed out — trying next model...")
            last_error = f"{model} timed out"
            continue

        except Exception as e:
            print(f"❌ Unexpected error with {model}: {e}")
            last_error = str(e)
            continue

    # All models failed
    raise HTTPException(
        status_code=503,
        detail=(
            f"All free models are currently rate-limited or unavailable. "
            f"Last error: {last_error}. "
            f"Please wait 60 seconds and try again — free tier limits reset every minute."
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response Models
# ─────────────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    product_description: Optional[str] = None
    reviews: Optional[List[str]] = None

class AnalyzeResponse(BaseModel):
    product_name: str
    source: str
    review_count: int
    blind_spots: List[str]
    weak_signals: List[str]
    opportunities: List[str]
    strategic_insights: List[str]


# ─────────────────────────────────────────────────────────────────────────────
# Scrapers
# ─────────────────────────────────────────────────────────────────────────────

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

SKIP_WORDS = [
    "cookie", "privacy", "terms", "sign in", "log in",
    "newsletter", "subscribe", "©", "all rights reserved",
    "product hunt", "trustpilot", "filter", "sort by",
]


def clean_reviews(paragraphs: list, min_len=50, max_len=800) -> list:
    """Deduplicate and filter paragraphs into real reviews."""
    seen, result = set(), []
    for text in paragraphs:
        text = text.strip()
        if (
            min_len < len(text) < max_len
            and text not in seen
            and not any(s in text.lower() for s in SKIP_WORDS)
        ):
            seen.add(text)
            result.append(text)
    return result[:25]


def scrape_product_hunt(url: str) -> dict:
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(400, f"Could not load Product Hunt page: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Product name
    product_name = "Unknown Product"
    title = soup.find("title")
    if title:
        product_name = title.text.split(" - ")[0].split(" | ")[0].strip()

    # Description
    description = f"Product from Product Hunt: {product_name}"
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = meta["content"].strip()

    # Reviews from paragraphs
    raw = [p.get_text(strip=True) for p in soup.find_all("p")]
    reviews = clean_reviews(raw)

    if not reviews:
        raise HTTPException(
            422,
            "Could not extract reviews from this Product Hunt URL. "
            "Product Hunt loads reviews via JavaScript which cannot be scraped this way. "
            "Please switch to 'Enter Manually' and paste the reviews yourself."
        )

    return {"product_name": product_name, "product_description": description,
            "reviews": reviews, "source": "Product Hunt"}


def scrape_trustpilot(url):
    # Extract domain from URL
    # e.g. https://www.trustpilot.com/review/notion.so → notion.so
    domain = url.split("/review/")[-1].strip("/")
    
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
    
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "trustpilot",
                "domain": domain,
                "api_key": SERPAPI_KEY,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        
        # Extract reviews from response
        reviews = []
        for review in data.get("reviews", []):
            text = review.get("text", "").strip()
            if text and len(text) > 20:
                reviews.append(text)
                
        if not reviews:
            raise HTTPException(422, "No reviews found. Try Enter Manually instead.")
            
        # Get company name
        product_name = data.get("company", {}).get("name", domain)
        
        return {
            "product_name": product_name,
            "product_description": f"Reviews from Trustpilot for {product_name}",
            "reviews": reviews[:25],
            "source": "Trustpilot via SerpApi",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"SerpApi error: {e}")

def scrape_url(url: str) -> dict:
    # ── Auto-fix common URL mistakes ──────────────────────────────────────────
    url = url.strip()

    # Remove accidental leading/trailing quotes users sometimes paste
    url = url.strip('"').strip("'")

    # Add https:// if user typed just the domain or path
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    # Normalise http → https
    if url.startswith("http://"):
        url = "https://" + url[7:]

    print(f"🔗 Scraping URL: {url}")

    if "producthunt.com" in url:
        return scrape_product_hunt(url)
    elif "trustpilot.com" in url:
        return scrape_trustpilot(url)
    else:
        raise HTTPException(
            400,
            "Only producthunt.com and trustpilot.com are supported right now. "
            "Use 'Enter Manually' for other sources."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Gap Analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_reviews(product_name: str, product_description: str, reviews: List[str]) -> dict:

    reviews_block = "\n\n".join(
        [f"Review {i+1}: {r}" for i, r in enumerate(reviews)]
    )

    system = (
        "You are a senior product strategist working with early-stage founders. "
        "Your job is deep gap analysis — NOT summarization. "
        "Read between the lines. Find what users are NOT clearly communicating. "
        "Respond ONLY with a valid JSON object. No markdown. No explanation."
    )

    prompt = f"""Product Name: {product_name}
Product Description: {product_description}

User Reviews ({len(reviews)} total):
{reviews_block}

Return a JSON object with EXACTLY these 4 keys:

"blind_spots": 3-5 features or areas users almost never mention. Things invisible to them.

"weak_signals": 3-5 subtle frustrations buried in positive or neutral reviews. Look for words like "but", "although", "wish", "sometimes". These are cracks before the churn.

"opportunities": 3-5 unmet needs users hint at but never directly demand. What workarounds do they describe?

"strategic_insights": 3-5 specific, high-priority recommendations for the founder. What to fix or build first.

Rules:
- Be specific to THIS product and THESE reviews only
- No generic advice like "improve UX"
- Return ONLY the raw JSON object"""

    raw = call_llm(prompt, system)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    key_ok = OPENROUTER_API_KEY not in ("your-openrouter-key-here", "")
    return {
        "status":       "ok",
        "version":      "3.1.0",
        "openrouter_key": "✅ Set" if key_ok else "❌ NOT SET — paste your key into main.py",
        "models":       FREE_MODELS,
        "docs":         "http://localhost:8000/docs",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):

    if request.url:
        data                = scrape_url(request.url)
        product_name        = data["product_name"]
        product_description = data["product_description"]
        reviews             = data["reviews"]
        source              = data["source"]

    elif request.product_description and request.reviews:
        if not request.reviews:
            raise HTTPException(400, "Provide at least one review.")
        if len(request.reviews) > 100:
            raise HTTPException(400, "Maximum 100 reviews per request.")
        product_name        = "Your Product"
        product_description = request.product_description
        reviews             = request.reviews
        source              = "Manual Input"

    else:
        raise HTTPException(
            400,
            "Send either 'url' OR 'product_description' + 'reviews' in the request body."
        )

    try:
        insights = analyze_reviews(product_name, product_description, reviews)
    except json.JSONDecodeError:
        raise HTTPException(500, "Model returned invalid JSON. Please try again.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    return AnalyzeResponse(
        product_name=product_name,
        source=source,
        review_count=len(reviews),
        **insights,
    )
