"""
Scraper service — handles all review extraction from external platforms.
Completely separate from routing and analysis logic.
"""

import requests
import json
from bs4 import BeautifulSoup
from fastapi import HTTPException
from core.config import SERPAPI_KEY

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
    """Scrape product name, description and reviews from Product Hunt."""
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(400, f"Could not load Product Hunt page: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    product_name = "Unknown Product"
    title = soup.find("title")
    if title:
        product_name = title.text.split(" - ")[0].split(" | ")[0].strip()

    description = f"Product from Product Hunt: {product_name}"
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        description = meta["content"].strip()

    raw = [p.get_text(strip=True) for p in soup.find_all("p")]
    reviews = clean_reviews(raw)

    if not reviews:
        raise HTTPException(
            422,
            "No reviews found on this Product Hunt page. "
            "Use Enter Manually instead."
        )

    return {
        "product_name": product_name,
        "product_description": description,
        "reviews": reviews,
        "source": "Product Hunt",
    }


def scrape_trustpilot(url: str) -> dict:
    """Scrape reviews from Trustpilot using SerpApi Google search."""
    domain = url.split("/review/")[-1].strip("/")

    if not SERPAPI_KEY:
        raise HTTPException(
            500,
            "SERPAPI_KEY not set. Add it to your .env file and Render environment variables."
        )

    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": f"{domain} reviews site:trustpilot.com",
                "api_key": SERPAPI_KEY,
                "num": 10,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        reviews = []
        for result in data.get("organic_results", []):
            snippet = result.get("snippet", "").strip()
            if snippet and len(snippet) > 30:
                reviews.append(snippet)

        if not reviews:
            raise HTTPException(
                422,
                "No reviews found. Use Enter Manually instead."
            )

        return {
            "product_name": domain,
            "product_description": f"Trustpilot reviews for {domain}",
            "reviews": reviews[:20],
            "source": "Trustpilot",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, f"Could not fetch reviews: {str(e)}")


def scrape_url(url: str) -> dict:
    """Route URL to correct scraper based on domain."""
    url = url.strip().strip('"').strip("'")
    if not url.startswith("http"):
        url = "https://" + url

    print(f"🔗 Scraping: {url}")

    if "producthunt.com" in url:
        return scrape_product_hunt(url)
    if "trustpilot.com" in url:
        return scrape_trustpilot(url)

    raise HTTPException(
        400,
        "Only producthunt.com and trustpilot.com supported. "
        "Use Enter Manually for other sources."
    )
