# backend/core/agent.py
from __future__ import annotations
import re, json, time
from typing import Dict, Any, List
from dateutil import parser as dateparser
from sqlalchemy import text

from backend.db.connect import SessionLocal
from backend.core.tracing import add_step

# Simple noun→SKU map (expand later)
SKU_MAP = {
    "chair": "CHAIR-FOLD",
    "chairs": "CHAIR-FOLD",
    "tent": "TENT-20x20",
    "tents": "TENT-20x20",
    "table": "TABLE-8FT",
    "tables": "TABLE-8FT",
}

def _now_ms() -> int:
    return int(time.time() * 1000)

def _duration_days(start_s: str | None, end_s: str | None, fallback_days: int = 3) -> int:
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
    with SessionLocal() as s:
        rows = s.execute(text("SELECT key_name, value_json FROM policies")).mappings().all()
        out = {}
        for r in rows:
            val = r["value_json"]
            if isinstance(val, (str, bytes)):
                try:
                    val = json.loads(val)
                except Exception:
                    pass
            out[r["key_name"]] = val
        return out

def _fetch_rate_for_sku(sku: str) -> Dict[str, Any]:
    with SessionLocal() as s:
        r = s.execute(text("SELECT * FROM rates WHERE sku=:sku"), {"sku": sku}).mappings().first()
        if not r:
            raise ValueError(f"rate not found for {sku}")
        return dict(r)

def _fetch_name_for_sku(sku: str) -> str:
    with SessionLocal() as s:
        r = s.execute(text("SELECT name FROM inventory WHERE sku=:sku"), {"sku": sku}).mappings().first()
        return r["name"] if r else sku

def _compute(items: List[Dict[str, Any]], days: int, policies: Dict[str, Any]) -> Dict[str, Any]:
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

        line_items.append({
            "sku": sku,
            "name": name,
            "quantity": qty,
            "unit_price": round(unit, 2),
            "extended": extended,
        })
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

def run_quote_loop(run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point expected by routes/quote.py"""
    t0 = _now_ms()

    # 1) normalize
    msg = (payload.get("message") or "").strip()
    inferred = _infer_from_message(msg) if msg else {"items": []}

    items = payload.get("items") or []
    if not items and inferred["items"]:
        items = inferred["items"]
    if not items:
        items = [{"sku": "CHAIR-FOLD", "quantity": 100}]  # fallback demo

    days = _duration_days(payload.get("start_date"), payload.get("end_date"), fallback_days=3)
    add_step(run_id, "normalize", {"in": payload}, {"items": items, "days": days}, _now_ms() - t0)

    # 2) policies
    t1 = _now_ms()
    policies = _fetch_policies()
    add_step(run_id, "policies", {}, policies, _now_ms() - t1)

    # 3) pricing
    t2 = _now_ms()
    quote = _compute(items, days, policies)
    add_step(run_id, "pricing", {"items": items, "days": days}, quote, _now_ms() - t2)

    # 4) guardrails
    t3 = _now_ms()
    if quote["subtotal"] <= 0:
        raise ValueError("subtotal must be positive")
    add_step(run_id, "policy_guardrails", {}, quote, _now_ms() - t3)

    return quote
