"""
GapSight — Review Gap Analyzer v3.2
Powered by OpenRouter (free)
Get your free key at: https://openrouter.ai
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json, os, time

load_dotenv()

app = FastAPI(title="GapSight API", version="3.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_raw_key           = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_KEY = "".join(_raw_key.split())
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"

FREE_MODELS = [
    "openrouter/auto",
    "meta-llama/llama-3.3-70b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-27b-it:free",
    "arcee-ai/trinity-large-preview:free",
]

def call_llm(prompt: str, system: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "GapSight",
    }
    last_error = ""
    for model in FREE_MODELS:
        print(f"Trying model: {model}")
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
            resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            if resp.status_code == 401:
                raise HTTPException(401, "Invalid API key. Check your .env file.")
            if resp.status_code == 429:
                secs = resp.json().get("error",{}).get("metadata",{}).get("retry_after_seconds", 30)
                print(f"Rate limited ({secs}s) — trying next model...")
                last_error = f"{model} rate-limited"
                time.sleep(1)
                continue
            if not resp.ok:
                msg = resp.json().get("error",{}).get("message", resp.text)
                print(f"Error {resp.status_code}: {msg}")
                last_error = msg
                continue
            content = resp.json()["choices"][0]["message"]["content"].strip()
            print(f"Success with: {model}")
            return content
        except HTTPException:
            raise
        except requests.Timeout:
            print(f"Timeout — trying next model...")
            last_error = "timeout"
            continue
        except Exception as e:
            print(f"Error: {e}")
            last_error = str(e)
            continue
    raise HTTPException(503, f"All models unavailable. Last error: {last_error}. Wait 60s and retry.")

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

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
SKIP = ["cookie","privacy","terms","sign in","log in","newsletter","product hunt","trustpilot","filter","sort by","©"]

def clean_reviews(paras, min_len=50, max_len=800):
    seen, result = set(), []
    for t in paras:
        t = t.strip()
        if min_len < len(t) < max_len and t not in seen and not any(s in t.lower() for s in SKIP):
            seen.add(t)
            result.append(t)
    return result[:25]

def scrape_product_hunt(url):
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(400, f"Could not load Product Hunt page: {e}")
    soup = BeautifulSoup(r.text, "html.parser")
    name = "Unknown Product"
    t = soup.find("title")
    if t: name = t.text.split(" - ")[0].split(" | ")[0].strip()
    desc = f"Product from Product Hunt: {name}"
    m = soup.find("meta", attrs={"name": "description"})
    if m and m.get("content"): desc = m["content"].strip()
    reviews = clean_reviews([p.get_text(strip=True) for p in soup.find_all("p")])
    if not reviews:
        raise HTTPException(422, "No reviews found on this Product Hunt page. Use Enter Manually instead.")
    return {"product_name": name, "product_description": desc, "reviews": reviews, "source": "Product Hunt"}

def scrape_trustpilot(url):
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(400, f"Could not load Trustpilot page: {e}")
    soup = BeautifulSoup(r.text, "html.parser")
    name = "Unknown Company"
    h = soup.find("h1")
    if h: name = h.get_text(strip=True)
    reviews = []
    for tag in soup.find_all("p", attrs={"data-service-review-text-typography": True}):
        t = tag.get_text(strip=True)
        if len(t) > 20: reviews.append(t)
    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(sc.string or "")
            for item in (data if isinstance(data, list) else [data]):
                for rv in item.get("review", []):
                    b = rv.get("reviewBody","").strip()
                    if b and len(b) > 20: reviews.append(b)
        except: continue
    if not reviews:
        reviews = clean_reviews([p.get_text(strip=True) for p in soup.find_all("p")])
    seen, unique = set(), []
    for rv in reviews:
        if rv not in seen: seen.add(rv); unique.append(rv)
    reviews = unique[:25]
    if not reviews:
        raise HTTPException(422, "No reviews found on this Trustpilot page. Use Enter Manually instead.")
    return {"product_name": name, "product_description": f"Reviews for {name}", "reviews": reviews, "source": "Trustpilot"}

def scrape_url(url):
    url = url.strip().strip('"').strip("'")
    if not url.startswith("http"): url = "https://" + url
    print(f"Scraping: {url}")
    if "producthunt.com" in url: return scrape_product_hunt(url)
    if "trustpilot.com"  in url: return scrape_trustpilot(url)
    raise HTTPException(400, "Only producthunt.com and trustpilot.com supported. Use Enter Manually for others.")

def analyze_reviews(name, desc, reviews):
    block = "\n\n".join([f"Review {i+1}: {r}" for i,r in enumerate(reviews)])
    system = "You are a senior product strategist. Do deep gap analysis NOT summarization. Find what users are NOT saying. Return ONLY a valid JSON object, no markdown, no explanation."
    prompt = f"""Product: {name}
Description: {desc}
Reviews ({len(reviews)} total):
{block}

Return JSON with exactly these 4 keys:
"blind_spots": 3-5 features users almost never mention
"weak_signals": 3-5 subtle frustrations hidden in positive reviews
"opportunities": 3-5 unmet needs users hint at but never demand
"strategic_insights": 3-5 specific actionable recommendations for the founder

Be specific to THIS product only. No generic advice. Return ONLY the raw JSON object."""
    raw = call_llm(prompt, system)
    try: return json.loads(raw)
    except:
        cleaned = raw.replace("```json","").replace("```","").strip()
        return json.loads(cleaned)

@app.get("/")
def root():
    key_ok = bool(OPENROUTER_API_KEY)
    return {
        "status":  "ok",
        "version": "3.2.0",
        "key":     "Set" if key_ok else "NOT SET - add OPENROUTER_API_KEY to .env file",
        "models":  FREE_MODELS,
    }

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if req.url:
        d = scrape_url(req.url)
        name, desc, reviews, source = d["product_name"], d["product_description"], d["reviews"], d["source"]
    elif req.product_description and req.reviews:
        if not req.reviews: raise HTTPException(400, "Provide at least one review.")
        name, desc, reviews, source = "Your Product", req.product_description, req.reviews, "Manual"
    else:
        raise HTTPException(400, "Send url OR product_description+reviews.")
    try:
        insights = analyze_reviews(name, desc, reviews)
    except json.JSONDecodeError:
        raise HTTPException(500, "Model returned invalid JSON. Try again.")
    except HTTPException: raise
    except Exception as e: raise HTTPException(500, f"Failed: {e}")
    return AnalyzeResponse(product_name=name, source=source, review_count=len(reviews), **insights)
