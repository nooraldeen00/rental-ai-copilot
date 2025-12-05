"""
Item Parser Module for RentalAI Copilot
Handles intelligent parsing of customer messages to extract rental items and quantities.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# Comprehensive item synonyms mapping to SKUs
ITEM_SYNONYMS = {
    # Event/Party - Chairs
    "chair": ["CHAIR-FOLD-WHT"],
    "chairs": ["CHAIR-FOLD-WHT"],
    "folding chair": ["CHAIR-FOLD-WHT"],
    "white chair": ["CHAIR-FOLD-WHT"],
    "plastic chair": ["CHAIR-FOLD-WHT"],
    "chiavari": ["CHAIR-CHIAVARI"],
    "gold chair": ["CHAIR-CHIAVARI"],

    # Event/Party - Tables
    "table": ["TABLE-8FT-RECT"],
    "tables": ["TABLE-8FT-RECT"],
    "rectangular table": ["TABLE-8FT-RECT"],
    "8ft table": ["TABLE-8FT-RECT"],
    "8 ft table": ["TABLE-8FT-RECT"],
    "6ft table": ["TABLE-6FT-RECT"],
    "6 ft table": ["TABLE-6FT-RECT"],
    "round table": ["TABLE-60RND"],
    "60 inch table": ["TABLE-60RND"],
    "60in table": ["TABLE-60RND"],

    # Event/Party - Linens
    "tablecloth": ["LINEN-120RND-WHT"],
    "linen": ["LINEN-120RND-WHT"],
    "white linen": ["LINEN-120RND-WHT"],
    "black linen": ["LINEN-120RND-BLK"],

    # Event/Party - Tents
    "tent": ["TENT-20x20"],
    "tents": ["TENT-20x20"],
    "canopy": ["TENT-10x10"],
    "pop up tent": ["TENT-10x10"],
    "10x10 tent": ["TENT-10x10"],
    "20x20 tent": ["TENT-20x20"],
    "frame tent": ["TENT-20x20"],
    "40x60 tent": ["TENT-40x60"],
    "pole tent": ["TENT-40x60"],
    "large tent": ["TENT-40x60"],

    # Event/Party - Stages
    "stage": ["STAGE-4x8"],
    "platform": ["STAGE-4x8"],
    "stage platform": ["STAGE-4x8"],

    # Audio/Visual - Speakers
    "speaker": ["SPEAKER-PA-BASIC"],
    "speakers": ["SPEAKER-PA-BASIC"],
    "pa system": ["SPEAKER-PA-PRO"],
    "pa": ["SPEAKER-PA-PRO"],
    "sound system": ["SPEAKER-PA-PRO"],
    "audio system": ["SPEAKER-PA-PRO"],
    "professional speaker": ["SPEAKER-PA-PRO"],

    # Audio/Visual - Microphones
    "microphone": ["MIC-WIRELESS-HH"],
    "mic": ["MIC-WIRELESS-HH"],
    "wireless mic": ["MIC-WIRELESS-HH"],
    "handheld mic": ["MIC-WIRELESS-HH"],

    # Audio/Visual - Other
    "mixer": ["MIXER-8CH"],
    "audio mixer": ["MIXER-8CH"],
    "light": ["LIGHT-UPLIGHT-LED"],
    "lights": ["LIGHT-UPLIGHT-LED"],
    "uplight": ["LIGHT-UPLIGHT-LED"],
    "uplights": ["LIGHT-UPLIGHT-LED"],
    "led light": ["LIGHT-UPLIGHT-LED"],
    "projector": ["PROJECTOR-4K"],
    "4k projector": ["PROJECTOR-4K"],
    "screen": ["SCREEN-PROJ-120"],
    "projection screen": ["SCREEN-PROJ-120"],

    # Construction - Lifts
    "lift": ["LIFT-SCISSOR-19"],
    "scissor lift": ["LIFT-SCISSOR-19"],
    "19ft lift": ["LIFT-SCISSOR-19"],
    "26ft lift": ["LIFT-SCISSOR-26"],
    "boom lift": ["LIFT-BOOM-40"],
    "telescopic lift": ["LIFT-BOOM-40"],

    # Construction - Generators
    "generator": ["GEN-5KW"],
    "gen": ["GEN-5KW"],
    "portable generator": ["GEN-5KW"],
    "diesel generator": ["GEN-10KW-DIESEL"],
    "10kw generator": ["GEN-10KW-DIESEL"],

    # Construction - Other
    "compressor": ["COMPRESSOR-185CFM"],
    "air compressor": ["COMPRESSOR-185CFM"],
    "scaffold": ["SCAFFOLD-5x5x7"],
    "scaffolding": ["SCAFFOLD-5x5x7"],

    # Heavy Equipment
    "forklift": ["FORKLIFT-5K"],
    "fork lift": ["FORKLIFT-5K"],
    "skid steer": ["SKIDSTEER-1800"],
    "skidsteer": ["SKIDSTEER-1800"],
    "loader": ["SKIDSTEER-1800"],
    "excavator": ["EXCAVATOR-MINI"],
    "mini excavator": ["EXCAVATOR-MINI"],

    # Climate Control
    "heater": ["HEATER-PROPANE"],
    "propane heater": ["HEATER-PROPANE"],
    "fan": ["FAN-DRUM-36"],
    "drum fan": ["FAN-DRUM-36"],
}

# Word-based number parsing
WORD_NUMBERS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "dozen": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}


def similarity(a: str, b: str) -> float:
    """Calculate string similarity ratio (0.0 to 1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def parse_quantity(text: str) -> Optional[int]:
    """
    Parse quantity from text, handling both numeric and word-based quantities.
    Examples: "50", "ten", "a dozen", "hundred"
    """
    text_lower = text.lower().strip()

    # Try direct number conversion first
    try:
        return int(text_lower)
    except ValueError:
        pass

    # Try word-based numbers
    if text_lower in WORD_NUMBERS:
        return WORD_NUMBERS[text_lower]

    # Handle compound numbers like "a dozen" or "a hundred"
    words = text_lower.split()
    if len(words) == 2 and words[0] in ["a", "an"] and words[1] in WORD_NUMBERS:
        return WORD_NUMBERS[words[1]]

    return None


def find_matching_sku(item_text: str, min_similarity: float = 0.6) -> Tuple[Optional[str], float]:
    """
    Find the best matching SKU for an item description using fuzzy matching.

    Args:
        item_text: The item description from customer message
        min_similarity: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        Tuple of (SKU, confidence_score) or (None, 0.0) if no match
    """
    item_lower = item_text.lower().strip()

    # First try exact match
    if item_lower in ITEM_SYNONYMS:
        sku = ITEM_SYNONYMS[item_lower][0]
        logger.debug(f"Exact match: '{item_text}' -> {sku}")
        return (sku, 1.0)

    # Try fuzzy matching against all synonyms
    best_match = None
    best_score = 0.0

    for synonym, skus in ITEM_SYNONYMS.items():
        score = similarity(item_lower, synonym)
        if score > best_score and score >= min_similarity:
            best_score = score
            best_match = skus[0]

    if best_match:
        logger.debug(f"Fuzzy match: '{item_text}' -> {best_match} (score: {best_score:.2f})")
    else:
        logger.debug(f"No match found for: '{item_text}' (best score: {best_score:.2f})")

    return (best_match, best_score)


def parse_items_from_message(message: str) -> List[Dict[str, Any]]:
    """
    Parse rental items and quantities from a customer message.

    Handles patterns like:
    - "50 chairs and 5 tables"
    - "ten speakers and a mixer"
    - "need 20 uplights"
    - "hundred chairs, dozen tables"

    Args:
        message: Customer's free-text request

    Returns:
        List of dicts with 'sku', 'quantity', and 'confidence' keys
    """
    logger.info(f"Parsing items from message: {message[:100]}...")

    items = []
    message_lower = message.lower()

    # Pattern 1: Numeric quantity + item (e.g., "50 chairs", "10 speakers")
    pattern1 = r'\b(\d+)\s+([a-z\s\-]+?)(?:\s+and\b|\s*,|\s*$)'
    for match in re.finditer(pattern1, message_lower):
        qty_text = match.group(1)
        item_text = match.group(2).strip()

        qty = parse_quantity(qty_text)
        if qty:
            sku, confidence = find_matching_sku(item_text)
            if sku:
                items.append({
                    "sku": sku,
                    "quantity": qty,
                    "confidence": confidence,
                    "source": f"{qty_text} {item_text}"
                })

    # Pattern 2: Word quantity + item (e.g., "ten speakers", "a dozen tables", "a mixer")
    word_qty_pattern = r'\b(' + '|'.join(WORD_NUMBERS.keys()) + r')\s+([a-z\s\-]+?)(?:\s+and\b|\s*,|\s*$)'
    for match in re.finditer(word_qty_pattern, message_lower):
        qty_text = match.group(1)
        item_text = match.group(2).strip()

        qty = parse_quantity(qty_text)
        if qty:
            sku, confidence = find_matching_sku(item_text)
            if sku:
                # Check if we already added this SKU (avoid duplicates from multiple patterns)
                if not any(item["sku"] == sku and item["quantity"] == qty for item in items):
                    items.append({
                        "sku": sku,
                        "quantity": qty,
                        "confidence": confidence,
                        "source": f"{qty_text} {item_text}"
                    })

    # Pattern 3: Standalone items without explicit quantity (assume 1)
    # Look for item names that weren't caught by quantity patterns
    for synonym, skus in ITEM_SYNONYMS.items():
        if synonym in message_lower:
            sku = skus[0]
            # Check if this SKU was already found with a quantity
            if not any(item["sku"] == sku for item in items):
                # Only add if it looks like a standalone mention
                if re.search(r'\b' + re.escape(synonym) + r'\b', message_lower):
                    items.append({
                        "sku": sku,
                        "quantity": 1,
                        "confidence": 0.7,  # Lower confidence for implicit quantity
                        "source": f"implicit: {synonym}"
                    })

    logger.info(
        f"Parsed {len(items)} items from message",
        extra={"extra_fields": {
            "item_count": len(items),
            "items": [{"sku": i["sku"], "qty": i["quantity"], "conf": i["confidence"]} for i in items]
        }}
    )

    return items


def extract_duration_hint(message: str) -> Optional[int]:
    """
    Try to extract rental duration from message text.

    Examples:
    - "for 3 days" -> 3
    - "5 day rental" -> 5
    - "weekend" -> 3 (Fri-Sun)
    - "week" -> 7

    Returns:
        Number of days or None if not found
    """
    message_lower = message.lower()

    # Pattern: "for N days" or "N day rental"
    day_match = re.search(r'\b(\d+)\s*days?\b', message_lower)
    if day_match:
        return int(day_match.group(1))

    # Pattern: "weekend" or "for the weekend"
    if re.search(r'\bweekend\b', message_lower):
        return 3

    # Pattern: "week" or "for a week"
    if re.search(r'\b(?:a|one)\s+week\b', message_lower):
        return 7

    # Pattern: "month"
    if re.search(r'\bmonth\b', message_lower):
        return 30

    return None
