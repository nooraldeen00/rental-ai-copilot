# backend/routes/quote.py
from __future__ import annotations

import json
from typing import Optional, Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text

from backend.models import QuoteRunPayload
from backend.core.tracing import start_run, add_step, finish_run
from backend.core.agent import run_quote_loop
from backend.db.connect import SessionLocal

router = APIRouter(prefix="/quote", tags=["quote"])


# ---------- Request Models (local to keep imports light) ----------

class FeedbackIn(BaseModel):
    run_id: int
    rating: int = Field(..., ge=1, le=5)
    note: Optional[str] = None


# ---------- Routes ----------

@router.post("/run")
def run_quote(req: QuoteRunPayload) -> Dict[str, Any]:
    """
    Kick off a quote run. Accepts freeform 'message' or structured fields.
    Creates a run, calls the agent loop, records steps, returns the computed quote.
    """
    # Prefer the user's message as the run "input", else synthesize a small summary
    input_text = req.message or (
        f"tier {req.customer_tier or 'C'} in {req.location or req.zip or 'unknown'} "
        f"{(req.start_date or '')} to {(req.end_date or '')}".strip()
    )

    run_id = start_run(input_text, req.seed or 0)

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
        out = run_quote_loop(run_id, payload)  # agent will add its own steps via add_step()
    except Exception as e:
        # record failure and surface a clear error
        add_step(run_id, "error", {"payload": payload}, {"error": str(e)}, 0)
        finish_run(run_id, cost=0.0)
        raise HTTPException(status_code=400, detail=f"quote failed: {e}")

    finish_run(run_id, cost=0.0)
    return {"run_id": run_id, "quote": out}


@router.post("/feedback")
def feedback(inb: FeedbackIn) -> Dict[str, Any]:
    """
    Demo policy: if rating <= 3, apply a 10% *non-taxable* goodwill discount
    to the latest quote object stored by steps(kind='policy_guardrails' or 'feedback_apply').
    We DO NOT modify 'subtotal' or recompute 'tax' here; we only reduce 'total'.
    """
    with SessionLocal() as s:
        step = s.execute(
            text("""
                SELECT output_json
                FROM steps
                WHERE run_id = :rid
                  AND kind IN ('policy_guardrails','feedback_apply')
                ORDER BY id DESC
                LIMIT 1
            """),
            {"rid": inb.run_id},
        ).mappings().first()

        if not step:
            raise HTTPException(status_code=404, detail="Run not found or not completed")

        raw = step["output_json"]
        quote = json.loads(raw) if isinstance(raw, (str, bytes)) else raw

        # Defensive shape handling
        try:
            subtotal = float(quote.get("subtotal", 0.0))
            total = float(quote.get("total", 0.0))
            fees: List[Dict[str, Any]] = list(quote.get("fees", []))
        except Exception:
            raise HTTPException(status_code=500, detail="Malformed quote payload in last step")

        if inb.rating <= 3 and subtotal > 0:
            discount = round(subtotal * 0.10, 2)
            # Add as a negative fee (non-taxable)
            fees.append({"rule": "goodwill_discount", "amount": -discount})
            quote["fees"] = fees
            quote["total"] = round(total - discount, 2)

            add_step(
                inb.run_id,
                "feedback_apply",
                {"rating": inb.rating, "note": inb.note},
                quote,
                0,
            )
            return {"run_id": inb.run_id, "quote": quote}

        # No discount applied; still record the feedback
        add_step(
            inb.run_id,
            "feedback_apply",
            {"rating": inb.rating, "note": inb.note},
            quote,
            0,
        )
        return {"run_id": inb.run_id, "quote": quote}


@router.get("/runs/{run_id}")
def get_run(run_id: int) -> Dict[str, Any]:
    """
    Inspect a run's step history (useful for debugging).
    """
    with SessionLocal() as s:
        rows = s.execute(
            text("""
                SELECT id, kind, input_json, output_json, duration_ms
                FROM steps
                WHERE run_id = :rid
                ORDER BY id
            """),
            {"rid": run_id},
        ).mappings().all()

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

        return {"run_id": run_id, "steps": steps}
