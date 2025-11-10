from pydantic import BaseModel
from typing import List, Optional, Any

class QuoteRequest(BaseModel):
    request_text: str
    customer_tier: str = "C"
    location: str
    zip: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    seed: Optional[int] = None

class FeedbackIn(BaseModel):
    run_id: int
    rating: int
    note: str

class LineItem(BaseModel):
    sku: str
    name: str
    qty: int
    daily: float
    total: float

class QuoteOut(BaseModel):
    line_items: List[LineItem]
    fees: List[dict]
    subtotal: float
    notes: List[str]
    citations: List[Any] = []
