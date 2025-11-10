import time
from typing import Dict, Any
from backend.core.tracing import add_step
from backend.core.tools import check_availability, get_rate, policy_guardrails

def run_quote_loop(run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    # naive parse: pick a default SKU and dates; replace with LLM later
    sku = payload.get("sku","LT-LED")
    qty = int(payload.get("qty", 2))
    duration_days = int(payload.get("duration_days", 3))
    location = payload.get("location","Dallas")

    step_in = {"sku": sku, "qty": qty, "days": duration_days, "location": location}
    avail = check_availability(sku, payload.get("start_date",""), payload.get("end_date",""), location)
    add_step(run_id, "availability", step_in, avail, int((time.time()-t0)*1000))

    t1 = time.time()
    rate = get_rate(sku, duration_days, payload.get("customer_tier","C"))
    add_step(run_id, "rate", {"sku": sku, "days": duration_days}, rate, int((time.time()-t1)*1000))

    li_total = rate["base_total"] * qty if rate.get("found") else 0.0
    quote = {
        "line_items": [{
            "sku": sku, "name": "LED Light Tower", "qty": qty,
            "daily": None, "total": round(li_total,2)
        }],
        "apply_waiver": True,
        "weekend_delivery": payload.get("weekend", False),
        "notes": []
    }

    t2 = time.time()
    guards = policy_guardrails(quote)
    quote["fees"] = guards["applied_adjustments"]
    quote["subtotal"] = guards["subtotal"]
    add_step(run_id, "policy_guardrails", quote, guards, int((time.time()-t2)*1000))

    quote["citations"] = ["availability","rates","policies"]
    return quote
