from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from backend.models import QuoteRequest, FeedbackIn, QuoteOut
from backend.core.tracing import start_run, add_step, finish_run
from backend.core.agent import run_quote_loop
from backend.db.connect import SessionLocal

router = APIRouter(prefix="/quote", tags=["quote"])

@router.post("/run")
def run_quote(req: QuoteRequest):
    run_id = start_run(req.request_text, req.seed)
    payload = {
        "sku": "LT-LED",   # TODO: later parse via LLM; for now fixed
        "qty": 2,
        "duration_days": 3,
        "location": req.location,
        "customer_tier": req.customer_tier,
        "weekend": False,
        "start_date": req.start_date,
        "end_date": req.end_date
    }
    out = run_quote_loop(run_id, payload)
    finish_run(run_id, cost=0.0)
    return {"run_id": run_id, "quote": out}

@router.post("/feedback")
def feedback(inb: FeedbackIn):
    # one-shot "improve": knock 10% off total if rating < 3; demo only
    with SessionLocal() as s:
        step = s.execute(text("SELECT output_json FROM steps WHERE run_id=:rid AND kind='policy_guardrails' ORDER BY id DESC LIMIT 1"),
                         {"rid": inb.run_id}).mappings().first()
        if not step:
            raise HTTPException(404, "Run not found or not completed")
        q = eval(step["output_json"])  # demo only; replace with JSON
        subtotal = q.get("subtotal",0.0)
        if inb.rating <= 3:
            discount = round(subtotal * 0.10,2)
            q["fees"].append({"rule":"goodwill_discount","amount":-discount})
            q["subtotal"] = round(subtotal - discount,2)
        add_step(inb.run_id, "feedback_apply", {"rating": inb.rating, "note": inb.note}, q, 0)
        return {"run_id": inb.run_id, "quote": q}
