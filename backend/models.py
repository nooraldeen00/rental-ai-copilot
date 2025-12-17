# backend/models.py
from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# ---------- Request payloads ----------


class QuoteItem(BaseModel):
    """Optional pre-parsed item (agent can also infer from free text)."""

    sku: Optional[str] = Field(
        None, description="Inventory SKU if known (e.g., CHAIR-FOLD)"
    )
    name: Optional[str] = Field(None, description="Human-readable item name")
    quantity: int = Field(..., ge=1, description="Requested quantity")
    notes: Optional[str] = None


class ServiceLocationMeta(BaseModel):
    """Metadata for selected service location."""
    zone: Optional[Literal["local", "regional", "extended"]] = None
    region: Optional[str] = None


class QuoteRunPayload(BaseModel):
    """
    Body for /runs/agent/quote.
    Either provide a freeform 'message' or structured fields below.
    The agent will normalize into items, dates, and location.
    """

    message: Optional[str] = Field(
        None,
        description="Freeform text like: 'Need 100 chairs in Plano Apr 12-14, Tier C, 75074'",
    )

    # Optional structured hints (agent can fill if omitted)
    customer_tier: Literal["A", "B", "C"] = "C"
    location: Optional[str] = None  # Legacy free-text location from request
    zip: Optional[str] = None
    start_date: Optional[str] = None  # ISO or natural lang parsed by agent
    end_date: Optional[str] = None
    seed: Optional[int] = None

    # New location resolution fields
    selected_service_location_id: Optional[str] = Field(
        None, description="ID of selected service location (e.g., 'dallas-tx')"
    )
    selected_service_location_label: Optional[str] = Field(
        None, description="Display label of selected location (e.g., 'Dallas, TX')"
    )
    selected_service_location_meta: Optional[ServiceLocationMeta] = Field(
        None, description="Zone and region metadata for selected location"
    )

    # Optional pre-specified items (agent can merge with inferred items)
    items: Optional[List[QuoteItem]] = None

    # Language for AI summary generation
    language: Optional[str] = Field(
        None, description="Language code for AI summary (e.g., 'en-US', 'es-ES')"
    )


class ResolvedLocation(BaseModel):
    """Result of location resolution and reconciliation."""
    location_free_text: Optional[str] = Field(
        None, description="Location extracted from customer's free-text request"
    )
    location_selected: Optional[str] = Field(
        None, description="Location selected from dropdown (label)"
    )
    location_selected_id: Optional[str] = Field(
        None, description="ID of selected location"
    )
    location_selected_meta: Optional[ServiceLocationMeta] = Field(
        None, description="Zone/region metadata for selected location"
    )
    location_final: str = Field(
        ..., description="Canonical location used for pricing and fees"
    )
    location_conflict: bool = Field(
        False, description="True if free_text and selected location appear to disagree"
    )
    conflict_message: Optional[str] = Field(
        None, description="Human-readable explanation when conflict exists"
    )
    rationale: str = Field(
        ..., description="Short explanation for AI prompt usage"
    )


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
