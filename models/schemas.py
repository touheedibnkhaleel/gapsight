"""
Pydantic models for request/response validation.
Keeping schemas separate means they can be reused across routes.
"""

from pydantic import BaseModel
from typing import List, Optional


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
