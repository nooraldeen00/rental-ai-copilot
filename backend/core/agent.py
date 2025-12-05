from __future__ import annotations
import re, json, time, os
from typing import Dict, Any, List
from dateutil import parser as dateparser
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv
from openai import OpenAI
from openai import OpenAIError

from backend.db.connect import SessionLocal
from backend.core.tracing import add_step
from backend.core.logging_config import get_logger
from backend.core.exceptions import DatabaseError, AIServiceError, QuoteGenerationError

# Load .env so OPENAI_API_KEY is available
load_dotenv()

# Create logger
logger = get_logger(__name__)

# Create a single OpenAI client for this module
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment")
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)
logger.info("OpenAI client initialized successfully")

# Simple noun→SKU map (updated for enhanced seed data)
SKU_MAP = {
    "chair": "CHAIR-FOLD-WHT",
    "chairs": "CHAIR-FOLD-WHT",
    "tent": "TENT-20x20",
    "tents": "TENT-20x20",
    "table": "TABLE-8FT-RECT",
    "tables": "TABLE-8FT-RECT",
}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _duration_days(
    start_s: str | None, end_s: str | None, fallback_days: int = 3
) -> int:
    try:
        if not start_s or not end_s:
            return fallback_days
        start = dateparser.parse(start_s).date()
        end = dateparser.parse(end_s).date()
        return max(1, (end - start).days + 1)
    except Exception:
        return fallback_days


def _infer_from_message(msg: str) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for m in re.finditer(r"(\d+)\s+(chairs?|tents?|tables?)", msg.lower()):
        qty = int(m.group(1))
        noun = m.group(2)
        sku = SKU_MAP.get(noun)
        if sku:
            items.append({"sku": sku, "quantity": qty})
    zip_m = re.search(r"\b(\d{5})\b", msg)
    return {"items": items, "zip": zip_m.group(1) if zip_m else None}


def _fetch_policies() -> Dict[str, Any]:
    logger.debug("Fetching pricing policies from database")
    try:
        with SessionLocal() as s:
            rows = (
                s.execute(text("SELECT key_name, value_json FROM policies"))
                .mappings()
                .all()
            )
            out = {}
            for r in rows:
                val = r["value_json"]
                if isinstance(val, (str, bytes)):
                    try:
                        val = json.loads(val)
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse policy {r['key_name']}: {str(e)}"
                        )
                        pass
                out[r["key_name"]] = val
            logger.info(f"Loaded {len(out)} pricing policies")
            return out
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching policies: {str(e)}", exc_info=True)
        raise DatabaseError("Failed to fetch pricing policies", details={"error": str(e)})


def _fetch_rate_for_sku(sku: str) -> Dict[str, Any]:
    logger.debug(f"Fetching rate for SKU: {sku}")
    try:
        with SessionLocal() as s:
            r = (
                s.execute(text("SELECT * FROM rates WHERE sku=:sku"), {"sku": sku})
                .mappings()
                .first()
            )
            if not r:
                logger.warning(f"No rate found for SKU: {sku}")
                raise ValueError(f"rate not found for {sku}")
            logger.debug(f"Found rate for SKU {sku}: daily=${r.get('daily')}")
            return dict(r)
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching rate for SKU {sku}: {str(e)}", exc_info=True)
        raise DatabaseError(f"Failed to fetch rate for SKU {sku}", details={"sku": sku, "error": str(e)})


def _fetch_name_for_sku(sku: str) -> str:
    logger.debug(f"Fetching inventory name for SKU: {sku}")
    try:
        with SessionLocal() as s:
            r = (
                s.execute(text("SELECT name FROM inventory WHERE sku=:sku"), {"sku": sku})
                .mappings()
                .first()
            )
            name = r["name"] if r else sku
            if not r:
                logger.warning(f"No inventory item found for SKU {sku}, using SKU as name")
            return name
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching inventory name for SKU {sku}: {str(e)}", exc_info=True)
        return sku  # Fallback to SKU if database fails


def _compute(
    items: List[Dict[str, Any]], days: int, policies: Dict[str, Any]
) -> Dict[str, Any]:
    line_items = []
    subtotal = 0.0
    max_delivery = 0.0

    for it in items:
        sku = it["sku"]
        qty = int(it["quantity"])
        rate = _fetch_rate_for_sku(sku)
        name = _fetch_name_for_sku(sku)

        unit = float(rate["daily"]) * days  # simple: daily * days (improve later)
        extended = round(unit * qty, 2)
        max_delivery = max(max_delivery, float(rate["delivery_fee_base"]))

        line_items.append(
            {
                "sku": sku,
                "name": name,
                "quantity": qty,
                "unit_price": round(unit, 2),
                "extended": extended,
            }
        )
        subtotal += extended

    subtotal = round(subtotal, 2)
    fees = []

    # damage waiver
    dw_pct = float((policies.get("default_damage_waiver") or {}).get("pct", 0.0))
    damage_waiver = round(subtotal * dw_pct / 100.0, 2) if dw_pct else 0.0
    if damage_waiver:
        fees.append({"rule": "damage_waiver", "amount": damage_waiver})

    # one delivery fee for the whole order (max of line bases)
    delivery_fee = round(max_delivery, 2) if max_delivery else 0.0
    if delivery_fee:
        fees.append({"rule": "delivery_fee_base", "amount": delivery_fee})

    taxable = subtotal + damage_waiver + delivery_fee
    tax_pct = float((policies.get("tax_rate") or {}).get("pct", 0.0))
    tax = round(taxable * tax_pct / 100.0, 2) if tax_pct else 0.0

    total = round(taxable + tax, 2)

    return {
        "line_items": line_items,
        "subtotal": subtotal,
        "fees": fees,
        "tax": tax,
        "total": total,
        "days": days,
    }

from typing import Dict, Any, List

def run_quote_loop(run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(
        f"Starting quote generation loop for run {run_id}",
        extra={
            "extra_fields": {
                "run_id": run_id,
                "has_message": bool(payload.get("message")),
                "has_items": bool(payload.get("items")),
                "customer_tier": payload.get("customer_tier"),
            }
        },
    )

    msg = (payload.get("message") or "").strip()
    inferred = _infer_from_message(msg) if msg else {"items": []}

    items = payload.get("items") or []
    used_inferred = False
    used_fallback = False

    if not items and inferred["items"]:
        items = inferred["items"]
        used_inferred = True
        logger.info(
            f"Inferred {len(items)} items from message for run {run_id}",
            extra={"extra_fields": {"run_id": run_id, "item_count": len(items)}},
        )

    if not items:
        # demo / safety fallback so the quote is never empty
        items = [{"sku": "CHAIR-FOLD-WHT", "quantity": 100}]
        used_fallback = True
        logger.warning(
            f"No items found, using fallback for run {run_id}",
            extra={"extra_fields": {"run_id": run_id}},
        )

    days = _duration_days(
        payload.get("start_date"), payload.get("end_date"), fallback_days=3
    )
    logger.debug(
        f"Calculated rental duration: {days} days for run {run_id}",
        extra={"extra_fields": {"run_id": run_id, "days": days}},
    )

    add_step(
        run_id,
        "normalize",
        {"payload": payload},
        {"items": items, "days": days},
        0,
    )

    # 2) pricing policies
    logger.debug(f"Fetching pricing policies for run {run_id}")
    t1 = _now_ms()
    try:
        policies = _fetch_policies()
        latency = _now_ms() - t1
        add_step(run_id, "policies", {}, policies, latency)
        logger.info(
            f"Loaded pricing policies for run {run_id} ({latency}ms)",
            extra={"extra_fields": {"run_id": run_id, "latency_ms": latency}},
        )
    except Exception as e:
        logger.error(
            f"Failed to fetch policies for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"run_id": run_id}},
        )
        raise

    # 3) pricing
    logger.debug(f"Computing quote pricing for run {run_id}")
    t2 = _now_ms()
    try:
        quote = _compute(items, days, policies)
        logger.info(
            f"Quote computed for run {run_id}: subtotal=${quote.get('subtotal')}, total=${quote.get('total')}",
            extra={
                "extra_fields": {
                    "run_id": run_id,
                    "subtotal": quote.get("subtotal"),
                    "total": quote.get("total"),
                    "item_count": len(quote.get("line_items", [])),
                }
            },
        )
    except Exception as e:
        logger.error(
            f"Failed to compute quote for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"run_id": run_id}},
        )
        raise

    # ---------- build AI-style notes ----------
    notes: List[str] = []

    if used_inferred:
        notes.append("Inferred rental items from the renter message.")
    if used_fallback:
        notes.append("Applied a default chair package so the quote is never empty.")

    # Note about duration
    if payload.get("start_date") or payload.get("end_date"):
        notes.append(f"Assumed {days} rental day(s) based on the provided dates.")
    else:
        notes.append(f"Assumed a default rental duration of {days} day(s).")

    # Note about tier
    tier = payload.get("customer_tier") or "C"
    notes.append(f"Applied pricing and policies for customer tier {tier}.")

    quote["notes"] = notes
    # ---------- END NEW NOTES ----------

    add_step(run_id, "pricing", {"items": items, "days": days}, quote, _now_ms() - t2)

    # 4) guardrails
    logger.debug(f"Applying policy guardrails for run {run_id}")
    t3 = _now_ms()
    if quote["subtotal"] <= 0:
        logger.error(
            f"Guardrail violation for run {run_id}: subtotal must be positive",
            extra={"extra_fields": {"run_id": run_id, "subtotal": quote["subtotal"]}},
        )
        raise ValueError("subtotal must be positive")
    latency = _now_ms() - t3
    add_step(run_id, "policy_guardrails", {}, quote, latency)
    logger.info(
        f"Policy guardrails passed for run {run_id}",
        extra={"extra_fields": {"run_id": run_id}},
    )

        # ---------- build AI-style notes ----------
    notes: List[str] = []

    if used_inferred:
        notes.append("Inferred rental items from the renter message.")
    if used_fallback:
        notes.append("Applied a default chair package so the quote is never empty.")

    if payload.get("start_date") or payload.get("end_date"):
        notes.append(f"Assumed {days} rental day(s) based on the provided dates.")
    else:
        notes.append(f"Assumed a default rental duration of {days} day(s).")

    tier = payload.get("customer_tier") or "C"
    notes.append(f"Applied pricing and policies for customer tier {tier}.")

    #  Ask OpenAI for a one-sentence summary (optional, wrapped in try/except)
    logger.debug(f"Generating AI summary for run {run_id}")
    try:
        user_msg = payload.get("message") or "Customer rental request."
        ai_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a rental quote assistant. "
                        "Write ONE short, friendly sentence explaining the quote to a customer. "
                        "Do not mention internal SKUs or calculations, just the outcome."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Customer message: {user_msg}\n"
                        f"Subtotal: {quote['subtotal']}, Fees: {quote['fees']}, "
                        f"Tax: {quote['tax']}, Total: {quote['total']}."
                    ),
                },
            ],
        )
        explanation = ai_resp.choices[0].message.content.strip()
        notes.append(f"AI summary: {explanation}")
        logger.info(
            f"Generated AI summary for run {run_id}",
            extra={"extra_fields": {"run_id": run_id, "summary_length": len(explanation)}},
        )
    except OpenAIError as e:
        logger.error(
            f"OpenAI API error generating summary for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"run_id": run_id}},
        )
        notes.append("AI summary unavailable due to an internal error.")
    except Exception as e:
        logger.error(
            f"Unexpected error generating AI summary for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"run_id": run_id}},
        )
        notes.append("AI summary unavailable due to an internal error.")

    quote["notes"] = notes
    # ---------- END NEW NOTES ----------

    pricing_latency = _now_ms() - t2
    add_step(run_id, "pricing", {"items": items, "days": days}, quote, pricing_latency)

    logger.info(
        f"Quote generation loop completed successfully for run {run_id}",
        extra={
            "extra_fields": {
                "run_id": run_id,
                "subtotal": quote.get("subtotal"),
                "total": quote.get("total"),
                "pricing_latency_ms": pricing_latency,
            }
        },
    )

    return quote
