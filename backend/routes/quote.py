# backend/routes/quote.py
from __future__ import annotations

import json
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.models import QuoteRunPayload
from backend.core.tracing import start_run, add_step, finish_run
from backend.core.agent import run_quote_loop
from backend.db.connect import SessionLocal
from backend.core.logging_config import get_logger
from backend.core.exceptions import (
    DatabaseError,
    ResourceNotFoundError,
    QuoteGenerationError,
    ValidationError,
)

router = APIRouter(prefix="/quote", tags=["quote"])
logger = get_logger(__name__)


# ---------- Helper: adapt internal quote → UI shape ----------

def _adapt_quote_for_ui(raw: Dict[str, Any]) -> Dict[str, Any]:
    line_items = raw.get("line_items", []) or []

    items_ui: List[Dict[str, Any]] = []
    for li in line_items:
        items_ui.append(
            {
                "sku": li.get("sku"),
                "name": li.get("name"),
                "qty": li.get("quantity"),
                "unitPrice": li.get("unit_price"),
                "subtotal": li.get("extended"),
            }
        )

    return {
        "currency": raw.get("currency", "$"),
        "items": items_ui,
        "subtotal": raw.get("subtotal", 0.0),
        "tax": raw.get("tax", 0.0),
        "fees": raw.get("fees", []),
        "total": raw.get("total", 0.0),
        # optional human-facing notes if you add them later
        "notes": raw.get("notes", []),
    }


# ---------- Request Models (local to keep imports light) ----------


class FeedbackIn(BaseModel):
    run_id: int
    rating: int = Field(..., ge=1, le=5)
    note: Optional[str] = None


# ---------- Routes ----------


@router.post("/run")
def run_quote(req: QuoteRunPayload, request: Request) -> Dict[str, Any]:
    """
    Kick off a quote run. Accepts freeform 'message' or structured fields.
    Creates a run, calls the agent loop, records steps, returns the computed quote.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        f"Starting quote generation",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "customer_tier": req.customer_tier,
                "location": req.location,
                "zip": req.zip,
                "has_message": bool(req.message),
                "has_items": bool(req.items),
            }
        },
    )

    # Validate input
    if not req.message and not req.items:
        logger.warning(
            "Quote request missing both message and items",
            extra={"extra_fields": {"request_id": request_id}},
        )
        raise ValidationError(
            "Either 'message' or 'items' must be provided",
            details={"request_id": request_id},
        )

    # Prefer the user's message as the run "input", else synthesize a small summary
    input_text = req.message or (
        f"tier {req.customer_tier or 'C'} in {req.location or req.zip or 'unknown'} "
        f"{(req.start_date or '')} to {(req.end_date or '')}".strip()
    )

    try:
        run_id = start_run(input_text, req.seed or 0)
        logger.info(
            f"Created run {run_id}",
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
    except SQLAlchemyError as e:
        logger.error(
            f"Database error creating run: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id}},
        )
        raise DatabaseError(
            "Failed to create quote run in database",
            details={"request_id": request_id, "error": str(e)},
        )

    # Payload passed to the agent (keep keys flat/explicit)
    payload: Dict[str, Any] = {
        "location": req.location,
        "zip": req.zip,
        "customer_tier": req.customer_tier or "C",
        "start_date": req.start_date,
        "end_date": req.end_date,
        "message": req.message,
        "items": [i.model_dump() for i in (req.items or [])],
    }

    try:
        logger.info(
            f"Running quote agent for run {run_id}",
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
        out = run_quote_loop(run_id, payload)
        logger.info(
            f"Quote generation completed successfully for run {run_id}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "run_id": run_id,
                    "subtotal": out.get("subtotal"),
                    "total": out.get("total"),
                }
            },
        )
    except ValueError as e:
        logger.error(
            f"Validation error in quote generation for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
        add_step(run_id, "error", {"payload": payload}, {"error": str(e)}, 0)
        finish_run(run_id, cost=0.0)
        raise QuoteGenerationError(
            f"Invalid quote data: {str(e)}",
            details={"request_id": request_id, "run_id": run_id},
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in quote generation for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
        add_step(run_id, "error", {"payload": payload}, {"error": str(e)}, 0)
        finish_run(run_id, cost=0.0)
        raise QuoteGenerationError(
            "Failed to generate quote",
            details={"request_id": request_id, "run_id": run_id, "error": str(e)},
        )

    try:
        ui_quote = _adapt_quote_for_ui(out)
        finish_run(run_id, cost=0.0)
        logger.info(
            f"Quote run {run_id} completed and returned to client",
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
        return {"run_id": run_id, "quote": ui_quote}
    except Exception as e:
        logger.error(
            f"Error adapting quote for UI: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
        raise QuoteGenerationError(
            "Failed to format quote response",
            details={"request_id": request_id, "run_id": run_id, "error": str(e)},
        )


@router.post("/feedback")
def feedback(inb: FeedbackIn, request: Request) -> Dict[str, Any]:
    """
    Demo policy: if rating <= 3, apply a 10% *non-taxable* goodwill discount
    to the latest quote object stored by steps(kind='policy_guardrails' or 'feedback_apply').
    We DO NOT modify 'subtotal' or recompute 'tax' here; we only reduce 'total'.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        f"Processing feedback for run {inb.run_id}",
        extra={
            "extra_fields": {
                "request_id": request_id,
                "run_id": inb.run_id,
                "rating": inb.rating,
                "has_note": bool(inb.note),
            }
        },
    )

    try:
        with SessionLocal() as s:
            step = (
                s.execute(
                    text(
                        """
                    SELECT output_json
                    FROM steps
                    WHERE run_id = :rid
                      AND kind IN ('policy_guardrails','feedback_apply')
                    ORDER BY id DESC
                    LIMIT 1
                """
                    ),
                    {"rid": inb.run_id},
                )
                .mappings()
                .first()
            )

            if not step:
                logger.warning(
                    f"Run {inb.run_id} not found for feedback",
                    extra={
                        "extra_fields": {"request_id": request_id, "run_id": inb.run_id}
                    },
                )
                raise ResourceNotFoundError("Run", inb.run_id)

            raw = step["output_json"]
            quote = json.loads(raw) if isinstance(raw, (str, bytes)) else raw

            # Defensive shape handling
            try:
                subtotal = float(quote.get("subtotal", 0.0))
                total = float(quote.get("total", 0.0))
                fees: List[Dict[str, Any]] = list(quote.get("fees", []))
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Malformed quote data for run {inb.run_id}: {str(e)}",
                    exc_info=True,
                    extra={
                        "extra_fields": {"request_id": request_id, "run_id": inb.run_id}
                    },
                )
                raise QuoteGenerationError(
                    "Malformed quote data in database",
                    details={"request_id": request_id, "run_id": inb.run_id},
                )

            # Apply discount only for low ratings
            if inb.rating <= 3 and subtotal > 0:
                discount = round(subtotal * 0.10, 2)
                # Add as a negative fee (non-taxable)
                fees.append({"rule": "goodwill_discount", "amount": -discount})
                quote["fees"] = fees
                quote["total"] = round(total - discount, 2)
                logger.info(
                    f"Applied goodwill discount of ${discount} for run {inb.run_id}",
                    extra={
                        "extra_fields": {
                            "request_id": request_id,
                            "run_id": inb.run_id,
                            "discount": discount,
                        }
                    },
                )

            # Always adapt to UI + record feedback
            ui_quote = _adapt_quote_for_ui(quote)
            add_step(
                inb.run_id,
                "feedback_apply",
                {"rating": inb.rating, "note": inb.note},
                ui_quote,
                0,
            )
            finish_run(inb.run_id, 0.0)

            logger.info(
                f"Feedback processed successfully for run {inb.run_id}",
                extra={
                    "extra_fields": {"request_id": request_id, "run_id": inb.run_id}
                },
            )

            return {"run_id": inb.run_id, "quote": ui_quote}

    except SQLAlchemyError as e:
        logger.error(
            f"Database error processing feedback for run {inb.run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id, "run_id": inb.run_id}},
        )
        raise DatabaseError(
            "Failed to process feedback",
            details={"request_id": request_id, "run_id": inb.run_id, "error": str(e)},
        )


@router.get("/runs/{run_id}")
def get_run(run_id: int, request: Request) -> Dict[str, Any]:
    """
    Inspect a run's step history (useful for debugging).
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.info(
        f"Fetching run history for run {run_id}",
        extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
    )

    try:
        with SessionLocal() as s:
            rows = (
                s.execute(
                    text(
                        """
                    SELECT id, kind, input_json, output_json, latency_ms
                    FROM steps
                    WHERE run_id = :rid
                    ORDER BY id
                """
                    ),
                    {"rid": run_id},
                )
                .mappings()
                .all()
            )

            if not rows:
                logger.warning(
                    f"No steps found for run {run_id}",
                    extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
                )
                raise ResourceNotFoundError("Run", run_id)

            # Convert output_json/input_json to objects when they are strings (SQLite/MySQL raw)
            steps: List[Dict[str, Any]] = []
            for r in rows:
                rec = dict(r)
                for key in ("input_json", "output_json"):
                    val = rec.get(key)
                    if isinstance(val, (str, bytes)):
                        try:
                            rec[key] = json.loads(val)
                        except Exception:
                            # Keep raw string if not valid JSON
                            pass
                steps.append(rec)

            logger.info(
                f"Retrieved {len(steps)} steps for run {run_id}",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "run_id": run_id,
                        "step_count": len(steps),
                    }
                },
            )

            return {"run_id": run_id, "steps": steps}

    except SQLAlchemyError as e:
        logger.error(
            f"Database error fetching run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"request_id": request_id, "run_id": run_id}},
        )
        raise DatabaseError(
            "Failed to fetch run history",
            details={"request_id": request_id, "run_id": run_id, "error": str(e)},
        )
