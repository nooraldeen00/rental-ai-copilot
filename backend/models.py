# backend/models.py
from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# ---------- Request payloads ----------

class QuoteItem(BaseModel):
    """Optional pre-parsed item (agent can also infer from free text)."""
    sku: Optional[str] = Field(None, description="Inventory SKU if known (e.g., CHAIR-FOLD)")
    name: Optional[str] = Field(None, description="Human-readable item name")
    quantity: int = Field(..., ge=1, description="Requested quantity")
    notes: Optional[str] = None

class QuoteRunPayload(BaseModel):
    """
    Body for /runs/agent/quote.
    Either provide a freeform 'message' or structured fields below.
    The agent will normalize into items, dates, and location.
    """
    message: Optional[str] = Field(
        None,
        description="Freeform text like: 'Need 100 chairs in Plano Apr 12-14, Tier C, 75074'"
    )

    # Optional structured hints (agent can fill if omitted)
    customer_tier: Literal['A', 'B', 'C'] = 'C'
    location: Optional[str] = None
    zip: Optional[str] = None
    start_date: Optional[str] = None   # ISO or natural lang parsed by agent
    end_date: Optional[str] = None
    seed: Optional[int] = None

    # Optional pre-specified items (agent can merge with inferred items)
    items: Optional[List[QuoteItem]] = None


# ---------- Internal agent/response shapes (optional but handy) ----------

class LinePrice(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: float
    extended: float

class QuotePricing(BaseModel):
    subtotal: float
    damage_waiver: float = 0.0
    delivery_fee: float = 0.0
    tax: float = 0.0
    total: float = 0.0

class QuoteResult(BaseModel):
    items: List[LinePrice]
    pricing: QuotePricing
    meta: Dict[str, Any] = {}

class RunTraceStep(BaseModel):
    kind: str
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None

class QuoteRunResponse(BaseModel):
    quote: Dict[str, Any] = {}
    trace: List[Dict[str, Any]] = []
