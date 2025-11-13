from typing import Dict, Any, List
from sqlalchemy import text
from backend.db.connect import SessionLocal


def check_availability(sku: str, start: str, end: str, location: str) -> Dict[str, Any]:
    with SessionLocal() as s:
        row = (
            s.execute(
                text(
                    "SELECT on_hand, committed FROM inventory WHERE sku=:sku AND location=:loc"
                ),
                {"sku": sku, "loc": location},
            )
            .mappings()
            .first()
        )
        if not row:
            return {"available": False, "reason": "SKU/Location not found"}
        available = max(0, row["on_hand"] - row["committed"])
        return {"available": available > 0, "qty_available": available}


def get_rate(sku: str, duration_days: int, customer_tier: str) -> Dict[str, Any]:
    with SessionLocal() as s:
        row = (
            s.execute(
                text(
                    "SELECT daily, weekly, monthly, damage_waiver_pct, delivery_fee_base FROM rates WHERE sku=:sku"
                ),
                {"sku": sku},
            )
            .mappings()
            .first()
        )
        if not row:
            return {"found": False}
        # naive pricing: daily * days (improve later)
        price = float(row["daily"]) * duration_days
        return {
            "found": True,
            "base_total": price,
            "damage_waiver_pct": float(row["damage_waiver_pct"]) / 100.0,
            "delivery_fee_base": float(row["delivery_fee_base"]),
        }


def policy_guardrails(quote: Dict[str, Any]) -> Dict[str, Any]:
    # naive: always apply damage waiver to subtotal, weekend surcharge if any 'weekend' date flagged in input
    subtotal = sum(li["total"] for li in quote.get("line_items", []))
    adjustments: List[Dict[str, Any]] = []
    if quote.get("apply_waiver", True):
        waiver = round(subtotal * 0.10, 2)
        adjustments.append({"rule": "damage_waiver_default", "amount": waiver})
        subtotal += waiver
    if quote.get("weekend_delivery", False):
        adjustments.append({"rule": "weekend_delivery_surcharge", "amount": 75.00})
        subtotal += 75.00
    return {
        "violations": [],
        "applied_adjustments": adjustments,
        "subtotal": round(subtotal, 2),
    }
