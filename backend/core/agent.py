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
from backend.core.item_parser import parse_items_from_message, extract_duration_hint

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


def _now_ms() -> int:
    return int(time.time() * 1000)


def _duration_days(
    start_s: str | None, end_s: str | None, message: str = "", fallback_days: int = 3
) -> int:
    """
    Calculate rental duration from dates or message hints.

    Args:
        start_s: Start date string
        end_s: End date string
        message: Customer message (may contain duration hints)
        fallback_days: Default duration if nothing is found

    Returns:
        Number of rental days
    """
    try:
        # First try explicit dates
        if start_s and end_s:
            start = dateparser.parse(start_s).date()
            end = dateparser.parse(end_s).date()
            days = max(1, (end - start).days + 1)
            logger.debug(f"Calculated duration from dates: {days} days ({start_s} to {end_s})")
            return days
    except Exception as e:
        logger.warning(f"Failed to parse dates: {str(e)}")

    # Try to extract from message
    if message:
        duration_hint = extract_duration_hint(message)
        if duration_hint:
            logger.debug(f"Extracted duration from message: {duration_hint} days")
            return duration_hint

    logger.debug(f"Using fallback duration: {fallback_days} days")
    return fallback_days


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
    items: List[Dict[str, Any]], days: int, policies: Dict[str, Any], tier: str = "C"
) -> Dict[str, Any]:
    """
    Compute quote pricing with tier discount support.

    Args:
        items: List of items with sku and quantity
        days: Rental duration in days
        policies: Pricing policies from database
        tier: Customer tier (A, B, or C)

    Returns:
        Quote dict with line_items, subtotal, fees, tax, total, and discount info
    """
    logger.debug(f"Computing quote: {len(items)} items, {days} days, tier {tier}")

    line_items = []
    subtotal = 0.0
    max_delivery = 0.0

    for it in items:
        sku = it["sku"]
        qty = int(it["quantity"])
        rate = _fetch_rate_for_sku(sku)
        name = _fetch_name_for_sku(sku)

        unit = float(rate["daily"]) * days
        extended = round(unit * qty, 2)
        max_delivery = max(max_delivery, float(rate["delivery_fee_base"]))

        line_items.append(
            {
                "sku": sku,
                "name": name,
                "qty": qty,  # Changed from 'quantity' to 'qty' for consistency with frontend
                "unitPrice": round(unit, 2),  # Changed from 'unit_price' to match frontend
                "subtotal": extended,  # Changed from 'extended' to match frontend
            }
        )
        subtotal += extended

    subtotal = round(subtotal, 2)

    # Apply tier discount
    tier_discounts = policies.get("tier_discounts", {})
    discount_pct = float(tier_discounts.get(tier, {}).get("pct", 0.0))
    discount_amount = round(subtotal * discount_pct / 100.0, 2)
    subtotal_after_discount = round(subtotal - discount_amount, 2)

    logger.info(
        f"Tier discount applied: {discount_pct}% for tier {tier}",
        extra={"extra_fields": {
            "tier": tier,
            "discount_pct": discount_pct,
            "discount_amount": discount_amount,
            "subtotal_before": subtotal,
            "subtotal_after": subtotal_after_discount
        }}
    )

    fees = []

    # Damage waiver (applied to discounted subtotal)
    dw_pct = float((policies.get("default_damage_waiver") or {}).get("pct", 0.0))
    damage_waiver = round(subtotal_after_discount * dw_pct / 100.0, 2) if dw_pct else 0.0
    if damage_waiver:
        fees.append({"name": "Damage Waiver", "amount": damage_waiver})

    # Delivery fee (one fee for the whole order)
    delivery_fee = round(max_delivery, 2) if max_delivery else 0.0
    if delivery_fee:
        fees.append({"name": "Delivery & Pickup", "amount": delivery_fee})

    # Tax calculation (on discounted subtotal + fees)
    taxable = subtotal_after_discount + damage_waiver + delivery_fee
    tax_pct = float((policies.get("tax_rate") or {}).get("pct", 0.0))
    tax = round(taxable * tax_pct / 100.0, 2) if tax_pct else 0.0

    total = round(taxable + tax, 2)

    return {
        "items": line_items,  # Changed from 'line_items' to 'items' for frontend consistency
        "subtotal": subtotal_after_discount,
        "subtotal_before_discount": subtotal,  # Keep track of original subtotal
        "discount_pct": discount_pct,
        "discount_amount": discount_amount,
        "fees": fees,
        "tax": tax,
        "total": total,
        "days": days,
    }


def run_quote_loop(run_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main quote generation loop with improved parsing and tier discounts.

    Args:
        run_id: Unique ID for this quote run
        payload: Request payload with message, dates, tier, language, etc.

    Returns:
        Quote dict with items, pricing, fees, and AI-generated notes
    """
    logger.info(
        f"Starting quote generation loop for run {run_id}",
        extra={
            "extra_fields": {
                "run_id": run_id,
                "has_message": bool(payload.get("message")),
                "has_items": bool(payload.get("items")),
                "customer_tier": payload.get("customer_tier"),
                "language": payload.get("language", "en-US"),
            }
        },
    )

    msg = (payload.get("message") or "").strip()
    tier = payload.get("customer_tier") or "C"
    language = payload.get("language") or "en-US"

    # Parse items from message using intelligent parser
    parsed_items = []
    unmatched_items = []
    used_parser = False
    used_fallback = False

    if msg:
        all_parsed = parse_items_from_message(msg)
        # Separate matched and unmatched items
        parsed_items = [i for i in all_parsed if i.get("matched", True) and i.get("sku")]
        unmatched_items = [i for i in all_parsed if not i.get("matched", True) or not i.get("sku")]

        if parsed_items:
            used_parser = True
            logger.info(
                f"Parsed {len(parsed_items)} matched items from message for run {run_id}",
                extra={"extra_fields": {
                    "run_id": run_id,
                    "message_preview": msg[:100],
                    "parsed_items": [{"sku": i["sku"], "qty": i["quantity"], "confidence": i["confidence"]} for i in parsed_items],
                    "unmatched_count": len(unmatched_items),
                }},
            )

        if unmatched_items:
            logger.warning(
                f"Found {len(unmatched_items)} unmatched items for run {run_id}",
                extra={"extra_fields": {
                    "run_id": run_id,
                    "unmatched_items": [{"name": i.get("unmatched_name"), "qty": i["quantity"]} for i in unmatched_items],
                }},
            )

    # Use explicit items from payload if provided, otherwise use parsed items
    items = payload.get("items") or []
    if not items and parsed_items:
        items = [{"sku": i["sku"], "quantity": i["quantity"]} for i in parsed_items]

    # Safety fallback if still no items
    if not items:
        items = [{"sku": "CHAIR-FOLD-WHT", "quantity": 100}]
        used_fallback = True
        logger.warning(
            f"No items found, using fallback for run {run_id}",
            extra={"extra_fields": {"run_id": run_id}},
        )

    # Calculate rental duration
    days = _duration_days(
        payload.get("start_date"),
        payload.get("end_date"),
        msg,
        fallback_days=3
    )
    logger.debug(
        f"Calculated rental duration: {days} days for run {run_id}",
        extra={"extra_fields": {"run_id": run_id, "days": days}},
    )

    add_step(
        run_id,
        "normalize",
        {"payload": payload},
        {"items": items, "days": days, "tier": tier},
        0,
    )

    # Fetch pricing policies
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

    # Compute quote with tier discounts
    logger.debug(f"Computing quote pricing for run {run_id}")
    t2 = _now_ms()
    try:
        quote = _compute(items, days, policies, tier)
        pricing_latency = _now_ms() - t2
        logger.info(
            f"Quote computed for run {run_id}: subtotal=${quote.get('subtotal')}, total=${quote.get('total')}",
            extra={
                "extra_fields": {
                    "run_id": run_id,
                    "subtotal": quote.get("subtotal"),
                    "total": quote.get("total"),
                    "item_count": len(quote.get("items", [])),
                    "discount_applied": quote.get("discount_amount", 0),
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

    add_step(run_id, "pricing", {"items": items, "days": days}, quote, pricing_latency)

    # Apply policy guardrails
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

    # Build AI-generated notes
    notes: List[str] = []

    # Language-specific labels for notes
    LANGUAGE_LABELS = {
        "en-US": {
            "parsing_note": "Intelligent parsing identified {count} equipment type(s) from your request.",
            "fallback_note": "Sample quote generated. Please specify your equipment needs for an accurate estimate.",
            "date_note": "Rental period: {days} day(s) based on your specified dates.",
            "duration_note": "Estimated {days}-day rental based on your request.",
            "unmatched_note": "Note: Could not match the following items: {items}. Please verify or contact us for assistance.",
            "ai_fallback": "Our AI quote assistant is temporarily unavailable, but your quote has been calculated accurately.",
            "ai_error": "Quote calculated successfully. Our team is ready to assist with any questions.",
        },
        "es-ES": {
            "parsing_note": "El análisis inteligente identificó {count} tipo(s) de equipo de su solicitud.",
            "fallback_note": "Cotización de muestra generada. Especifique sus necesidades de equipo para un presupuesto preciso.",
            "date_note": "Período de alquiler: {days} día(s) según las fechas especificadas.",
            "duration_note": "Alquiler estimado de {days} día(s) según su solicitud.",
            "unmatched_note": "Nota: No se pudieron encontrar los siguientes artículos: {items}. Verifique o contáctenos para asistencia.",
            "ai_fallback": "Nuestro asistente de cotización AI no está disponible temporalmente, pero su cotización se ha calculado con precisión.",
            "ai_error": "Cotización calculada exitosamente. Nuestro equipo está listo para ayudarle con cualquier pregunta.",
        },
        "ar-SA": {
            "parsing_note": "حدد التحليل الذكي {count} نوع(أنواع) من المعدات من طلبك.",
            "fallback_note": "تم إنشاء عرض أسعار نموذجي. يرجى تحديد احتياجاتك من المعدات للحصول على تقدير دقيق.",
            "date_note": "فترة الإيجار: {days} يوم(أيام) بناءً على التواريخ المحددة.",
            "duration_note": "إيجار تقديري لمدة {days} يوم(أيام) بناءً على طلبك.",
            "unmatched_note": "ملاحظة: لم نتمكن من مطابقة العناصر التالية: {items}. يرجى التحقق أو الاتصال بنا للمساعدة.",
            "ai_fallback": "مساعد عرض الأسعار الذكي غير متاح مؤقتًا، ولكن تم حساب عرض الأسعار الخاص بك بدقة.",
            "ai_error": "تم حساب عرض الأسعار بنجاح. فريقنا جاهز للمساعدة في أي أسئلة.",
        },
        "ja-JP": {
            "parsing_note": "インテリジェント解析により、リクエストから{count}種類の機器を特定しました。",
            "fallback_note": "サンプル見積もりが生成されました。正確な見積もりのために機器のニーズをご指定ください。",
            "date_note": "レンタル期間：指定された日付に基づく{days}日間。",
            "duration_note": "リクエストに基づく推定{days}日間のレンタル。",
            "unmatched_note": "注：以下のアイテムをマッチングできませんでした：{items}。確認するか、サポートにお問い合わせください。",
            "ai_fallback": "AI見積もりアシスタントは一時的に利用できませんが、見積もりは正確に計算されています。",
            "ai_error": "見積もりは正常に計算されました。ご質問がございましたら、チームがお手伝いいたします。",
        },
    }

    # Get language-specific labels (default to English)
    lang_key = language if language in LANGUAGE_LABELS else "en-US"
    labels = LANGUAGE_LABELS[lang_key]

    # Language name mapping for AI prompt
    LANGUAGE_NAMES = {
        "en-US": "English",
        "es-ES": "Spanish",
        "ar-SA": "Arabic",
        "ja-JP": "Japanese",
    }
    target_language = LANGUAGE_NAMES.get(language, "English")

    # Generate professional AI explanation
    logger.debug(f"Generating AI summary for run {run_id} in {target_language}")
    try:
        user_msg = payload.get("message") or "Customer rental request."

        # Build item summary for AI
        item_summary = ", ".join([f"{i['qty']}x {i['name']}" for i in quote['items'][:5]])
        if len(quote['items']) > 5:
            item_summary += f" (and {len(quote['items']) - 5} more items)"

        tier_names = {"A": "Premium", "B": "Corporate", "C": "Standard"}
        tier_name = tier_names.get(tier, "Standard")

        system_prompt = f"""You are a professional customer service representative for a premium rental equipment company.

Generate a concise, professional explanation of this quote that:
1. Acknowledges what the customer requested
2. Briefly explains the equipment provided
3. Mentions tier discount if applicable (but keep it subtle and professional)
4. Sounds warm, competent, and trustworthy - like a CSR from a high-end service company

IMPORTANT: You MUST write your response entirely in {target_language}. Do not use English unless the target language is English.

Keep it to 2-3 sentences maximum. Use professional but approachable language. Do not mention SKUs, internal codes, or technical calculation details."""

        user_prompt = f"""Customer request: "{user_msg}"

Equipment provided: {item_summary}
Rental duration: {days} day(s)
Customer tier: {tier_name} (tier {tier})
Discount applied: {quote['discount_pct']}%
Subtotal before discount: ${quote['subtotal_before_discount']:.2f}
Final total: ${quote['total']:.2f}

Remember: Write your response in {target_language}."""

        ai_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        explanation = ai_resp.choices[0].message.content.strip()
        notes.append(explanation)

        logger.info(
            f"Generated AI summary for run {run_id} in {target_language}",
            extra={"extra_fields": {"run_id": run_id, "summary_length": len(explanation), "language": language}},
        )
    except OpenAIError as e:
        logger.error(
            f"OpenAI API error generating summary for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"run_id": run_id}},
        )
        notes.append(labels["ai_fallback"])
    except Exception as e:
        logger.error(
            f"Unexpected error generating AI summary for run {run_id}: {str(e)}",
            exc_info=True,
            extra={"extra_fields": {"run_id": run_id}},
        )
        notes.append(labels["ai_error"])

    # Add technical notes for transparency (in selected language)
    if used_parser:
        notes.append(labels["parsing_note"].format(count=len(items)))
    if used_fallback:
        notes.append(labels["fallback_note"])

    # Add unmatched items note if any
    if unmatched_items:
        unmatched_names = ", ".join([i.get("unmatched_name", "unknown") for i in unmatched_items])
        notes.append(labels["unmatched_note"].format(items=unmatched_names))

    # Add duration note
    if payload.get("start_date") and payload.get("end_date"):
        notes.append(labels["date_note"].format(days=days))
    else:
        duration_hint = extract_duration_hint(msg) if msg else None
        if duration_hint:
            notes.append(labels["duration_note"].format(days=days))

    quote["notes"] = notes

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
