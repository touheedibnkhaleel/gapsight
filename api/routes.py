"""
API routes — handles HTTP only.
No business logic here. Just receives requests,
calls services, returns responses.
"""

import json
from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.scraper import scrape_url
from services.analyzer import analyze_reviews
from core.config import OPENROUTER_API_KEY, FREE_MODELS

router = APIRouter()


@router.get("/")
def root():
    """Health check endpoint."""
    key_ok = bool(OPENROUTER_API_KEY)
    return {
        "status":  "ok",
        "version": "4.0.0",
        "key":     "Set" if key_ok else "NOT SET — add OPENROUTER_API_KEY to .env",
        "models":  FREE_MODELS,
    }


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    """
    Analyze product reviews and return gap insights.

    Mode 1 — URL:    { "url": "https://www.producthunt.com/products/x" }
    Mode 2 — Manual: { "product_description": "...", "reviews": ["..."] }
    """

    # ── URL Mode ──
    if req.url:
        data                = scrape_url(req.url)
        product_name        = data["product_name"]
        product_description = data["product_description"]
        reviews             = data["reviews"]
        source              = data["source"]

    # ── Manual Mode ──
    # Using "is not None" to properly distinguish:
    # None = field not provided
    # []   = provided but empty
    # ""   = provided but empty string
    elif req.product_description is not None and req.reviews is not None:
        if not req.product_description.strip():
            raise HTTPException(400, "Provide a product description.")
        if len(req.product_description.strip()) < 10:
            raise HTTPException(400, "Product description is too short. Please describe your product properly.")
        if len(req.reviews) == 0:
            raise HTTPException(400, "Provide at least one review.")
        if len(req.reviews) > 100:
            raise HTTPException(400, "Maximum 100 reviews per request.")

        # Validate each review is real text not random characters
        valid_reviews = []
        for review in req.reviews:
            review = review.strip()
            # Must be at least 20 characters
            if len(review) < 20:
                continue
            # Must contain at least 3 real words (spaces between words)
            words = review.split()
            if len(words) < 3:
                continue
            # Must not be mostly random characters
            # Check: ratio of alphabetic characters must be > 60%
            alpha_count = sum(1 for c in review if c.isalpha())
            if len(review) > 0 and (alpha_count / len(review)) < 0.6:
                continue
            valid_reviews.append(review)

        if len(valid_reviews) == 0:
            raise HTTPException(
                400,
                "No valid reviews found. Please paste real user reviews — "
                "not random characters. Each review must be a proper sentence."
            )

        product_name        = "Your Product"
        product_description = req.product_description
        reviews             = valid_reviews
        source              = "Manual Input"

    else:
        raise HTTPException(
            400,
            "Send either 'url' OR 'product_description' + 'reviews'."
        )

    # ── Run Analysis ──
    try:
        insights = analyze_reviews(product_name, product_description, reviews)
    except json.JSONDecodeError:
        raise HTTPException(500, "Model returned invalid JSON. Try again.")
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
