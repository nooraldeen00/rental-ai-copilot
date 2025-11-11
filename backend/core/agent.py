# backend/core/agent.py
import re
from datetime import datetime
from dateutil import parser as dateparser
from typing import Tuple

from backend.models import QuoteRunPayload
from backend.core.llm import LLMClient
from backend.core.prompt import EXTRACT_SYSTEM, EXTRACT_USER_TEMPLATE

ZIP_RE = re.compile(r"\b(\d{5})(?:-\d{4})?\b", re.IGNORECASE)
TIER_RE = re.compile(r"\btier\s*([ABC])\b", re.IGNORECASE)
RANGE_SEP_RE = re.compile(r"\bto\b|\-|–|—|through|thru", re.IGNORECASE)

def _normalize_dates(start: str, end: str) -> Tuple[str, str]:
    def to_iso(s: str) -> str:
        d = dateparser.parse(s, fuzzy=True, dayfirst=False)
        return d.date().isoformat()
    s = to_iso(start)
    e = to_iso(end)
    if s > e:
        s, e = e, s
    return s, e

def _fallback_dates(text: str) -> Tuple[str, str]:
    parts = RANGE_SEP_RE.split(text)
    if len(parts) >= 2:
        left, right = parts[0], parts[-1]
        try:
            return _normalize_dates(left, right)
        except Exception:
            pass
    # single date
    try:
        d = dateparser.parse(text, fuzzy=True, dayfirst=False)
        if d:
            iso = d.date().isoformat()
            return iso, iso
    except Exception:
        pass
    today = datetime.now().date().isoformat()
    return today, today

def _validate_payload(d: dict, user_text: str) -> QuoteRunPayload:
    # Basic shape + guards
    req = d.get("request_text") or user_text
    tier = d.get("customer_tier") or ""
    loc  = d.get("location") or ""
    zipc = d.get("zip") or ""
    s    = d.get("start_date")
    e    = d.get("end_date")
    seed = d.get("seed", 0)

    # dates: if missing or unparsable, fallback
    if not s or not e:
        s, e = _fallback_dates(user_text)
    else:
        try:
            s, e = _normalize_dates(s, e)
        except Exception:
            s, e = _fallback_dates(user_text)

    # sanitize zip
    if zipc and not ZIP_RE.fullmatch(str(zipc)):
        zipc = ""

    # sanitize tier
    if tier and tier.upper() not in ("A","B","C"):
        tier = ""

    return QuoteRunPayload(
        request_text=req,
        customer_tier=tier.upper(),
        location=loc.strip(" ,."),
        zip=zipc,
        start_date=s,
        end_date=e,
        seed=int(seed) if isinstance(seed, int) else 0,
    )

class QuoteExtractor:
    @staticmethod
    def to_payload(user_text: str) -> QuoteRunPayload:
        llm = LLMClient()
        user = EXTRACT_USER_TEMPLATE.format(message=user_text)
        try:
            raw = llm.json_chat(EXTRACT_SYSTEM, user)
            return _validate_payload(raw, user_text)
        except Exception:
            # Fallback purely via heuristics if LLM fails
            s, e = _fallback_dates(user_text)
            zipc = (ZIP_RE.search(user_text) or [None, ""])[1]
            tierm = TIER_RE.search(user_text)
            tier = tierm.group(1).upper() if tierm else ""
            # naive loc heuristic
            m = re.search(r"\b(in|at)\s+([A-Za-z][A-Za-z\s\.,'-]+)", user_text, re.IGNORECASE)
            loc = m.group(2).strip(" ,.") if m else ""
            return QuoteRunPayload(
                request_text=user_text,
                customer_tier=tier,
                location=loc,
                zip=zipc,
                start_date=s,
                end_date=e,
                seed=0,
            )
