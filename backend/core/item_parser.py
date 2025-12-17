"""
Item Parser Module for RentalAI Copilot
Handles intelligent parsing of customer messages to extract rental items and quantities.

Key features:
- Robust extraction of quantity + item from natural language
- Support for: "50", "5x", "qty 5", "five", "dozen", etc.
- Handles compound phrases: "50 white folding chairs", "5 60-inch round tables"
- Normalizes size specifications: "60-inch", "60in", "60"", "60 inch"
- Fuzzy matching for item synonyms
- Returns unmatched items for transparency
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Tuple, Optional
from difflib import SequenceMatcher
from backend.core.logging_config import get_logger

logger = get_logger(__name__)

# Comprehensive item synonyms mapping to SKUs
# Priority order: more specific matches first
ITEM_SYNONYMS = {
    # Event/Party - Chairs (specific first)
    "white folding chair": ["CHAIR-FOLD-WHT"],
    "white folding chairs": ["CHAIR-FOLD-WHT"],
    "white plastic chair": ["CHAIR-FOLD-WHT"],
    "white plastic chairs": ["CHAIR-FOLD-WHT"],
    "folding chair white": ["CHAIR-FOLD-WHT"],
    "folding chairs white": ["CHAIR-FOLD-WHT"],
    "plastic folding chair": ["CHAIR-FOLD-WHT"],
    "plastic folding chairs": ["CHAIR-FOLD-WHT"],
    "folding chair": ["CHAIR-FOLD-WHT"],
    "folding chairs": ["CHAIR-FOLD-WHT"],
    "white chair": ["CHAIR-FOLD-WHT"],
    "white chairs": ["CHAIR-FOLD-WHT"],
    "plastic chair": ["CHAIR-FOLD-WHT"],
    "plastic chairs": ["CHAIR-FOLD-WHT"],
    "chair": ["CHAIR-FOLD-WHT"],
    "chairs": ["CHAIR-FOLD-WHT"],
    "chiavari chair": ["CHAIR-CHIAVARI"],
    "chiavari chairs": ["CHAIR-CHIAVARI"],
    "chiavari": ["CHAIR-CHIAVARI"],
    "gold chair": ["CHAIR-CHIAVARI"],
    "gold chairs": ["CHAIR-CHIAVARI"],

    # Event/Party - Tables (60" round - most variations)
    "60 inch round table": ["TABLE-60RND"],
    "60 inch round tables": ["TABLE-60RND"],
    "60-inch round table": ["TABLE-60RND"],
    "60-inch round tables": ["TABLE-60RND"],
    "60in round table": ["TABLE-60RND"],
    "60in round tables": ["TABLE-60RND"],
    '60" round table': ["TABLE-60RND"],
    '60" round tables': ["TABLE-60RND"],
    "60 round table": ["TABLE-60RND"],
    "60 round tables": ["TABLE-60RND"],
    "60-inch table": ["TABLE-60RND"],
    "60-inch tables": ["TABLE-60RND"],
    "60 inch table": ["TABLE-60RND"],
    "60 inch tables": ["TABLE-60RND"],
    "60in table": ["TABLE-60RND"],
    "60in tables": ["TABLE-60RND"],
    '60" table': ["TABLE-60RND"],
    '60" tables': ["TABLE-60RND"],
    "5 foot round table": ["TABLE-60RND"],
    "5 foot round tables": ["TABLE-60RND"],
    "5ft round table": ["TABLE-60RND"],
    "5ft round tables": ["TABLE-60RND"],
    "round table": ["TABLE-60RND"],
    "round tables": ["TABLE-60RND"],

    # Event/Party - Tables (8ft rectangular)
    "8ft rectangular table": ["TABLE-8FT-RECT"],
    "8ft rectangular tables": ["TABLE-8FT-RECT"],
    "8 ft rectangular table": ["TABLE-8FT-RECT"],
    "8 ft rectangular tables": ["TABLE-8FT-RECT"],
    "8-foot rectangular table": ["TABLE-8FT-RECT"],
    "8-foot rectangular tables": ["TABLE-8FT-RECT"],
    "8 foot rectangular table": ["TABLE-8FT-RECT"],
    "8 foot rectangular tables": ["TABLE-8FT-RECT"],
    "8ft banquet table": ["TABLE-8FT-RECT"],
    "8ft banquet tables": ["TABLE-8FT-RECT"],
    "8ft table": ["TABLE-8FT-RECT"],
    "8ft tables": ["TABLE-8FT-RECT"],
    "8 ft table": ["TABLE-8FT-RECT"],
    "8 ft tables": ["TABLE-8FT-RECT"],
    "8-foot table": ["TABLE-8FT-RECT"],
    "8-foot tables": ["TABLE-8FT-RECT"],
    "8 foot table": ["TABLE-8FT-RECT"],
    "8 foot tables": ["TABLE-8FT-RECT"],
    "rectangular table": ["TABLE-8FT-RECT"],
    "rectangular tables": ["TABLE-8FT-RECT"],
    "banquet table": ["TABLE-8FT-RECT"],
    "banquet tables": ["TABLE-8FT-RECT"],

    # Event/Party - Tables (6ft rectangular)
    "6ft rectangular table": ["TABLE-6FT-RECT"],
    "6ft rectangular tables": ["TABLE-6FT-RECT"],
    "6 ft rectangular table": ["TABLE-6FT-RECT"],
    "6 ft rectangular tables": ["TABLE-6FT-RECT"],
    "6-foot rectangular table": ["TABLE-6FT-RECT"],
    "6-foot rectangular tables": ["TABLE-6FT-RECT"],
    "6 foot rectangular table": ["TABLE-6FT-RECT"],
    "6 foot rectangular tables": ["TABLE-6FT-RECT"],
    "6ft table": ["TABLE-6FT-RECT"],
    "6ft tables": ["TABLE-6FT-RECT"],
    "6 ft table": ["TABLE-6FT-RECT"],
    "6 ft tables": ["TABLE-6FT-RECT"],
    "6-foot table": ["TABLE-6FT-RECT"],
    "6-foot tables": ["TABLE-6FT-RECT"],
    "6 foot table": ["TABLE-6FT-RECT"],
    "6 foot tables": ["TABLE-6FT-RECT"],

    # Generic table (default to 8ft)
    "table": ["TABLE-8FT-RECT"],
    "tables": ["TABLE-8FT-RECT"],

    # Event/Party - Linens
    "white tablecloth": ["LINEN-120RND-WHT"],
    "white tablecloths": ["LINEN-120RND-WHT"],
    "white linen": ["LINEN-120RND-WHT"],
    "white linens": ["LINEN-120RND-WHT"],
    "tablecloth": ["LINEN-120RND-WHT"],
    "tablecloths": ["LINEN-120RND-WHT"],
    "linen": ["LINEN-120RND-WHT"],
    "linens": ["LINEN-120RND-WHT"],
    "black tablecloth": ["LINEN-120RND-BLK"],
    "black tablecloths": ["LINEN-120RND-BLK"],
    "black linen": ["LINEN-120RND-BLK"],
    "black linens": ["LINEN-120RND-BLK"],

    # Event/Party - Tents
    "10x10 tent": ["TENT-10x10"],
    "10x10 tents": ["TENT-10x10"],
    "10 x 10 tent": ["TENT-10x10"],
    "10 x 10 tents": ["TENT-10x10"],
    "pop up tent": ["TENT-10x10"],
    "pop up tents": ["TENT-10x10"],
    "popup tent": ["TENT-10x10"],
    "popup tents": ["TENT-10x10"],
    "canopy": ["TENT-10x10"],
    "canopies": ["TENT-10x10"],
    "20x20 tent": ["TENT-20x20"],
    "20x20 tents": ["TENT-20x20"],
    "20 x 20 tent": ["TENT-20x20"],
    "20 x 20 tents": ["TENT-20x20"],
    "frame tent": ["TENT-20x20"],
    "frame tents": ["TENT-20x20"],
    "40x60 tent": ["TENT-40x60"],
    "40x60 tents": ["TENT-40x60"],
    "40 x 60 tent": ["TENT-40x60"],
    "40 x 60 tents": ["TENT-40x60"],
    "pole tent": ["TENT-40x60"],
    "pole tents": ["TENT-40x60"],
    "large tent": ["TENT-40x60"],
    "large tents": ["TENT-40x60"],
    "tent": ["TENT-20x20"],
    "tents": ["TENT-20x20"],

    # Event/Party - Stages
    "stage platform": ["STAGE-4x8"],
    "stage platforms": ["STAGE-4x8"],
    "stage": ["STAGE-4x8"],
    "stages": ["STAGE-4x8"],
    "platform": ["STAGE-4x8"],
    "platforms": ["STAGE-4x8"],

    # Audio/Visual - Speakers
    "professional pa system": ["SPEAKER-PA-PRO"],
    "professional pa systems": ["SPEAKER-PA-PRO"],
    "pro pa system": ["SPEAKER-PA-PRO"],
    "pro pa systems": ["SPEAKER-PA-PRO"],
    "professional speaker": ["SPEAKER-PA-PRO"],
    "professional speakers": ["SPEAKER-PA-PRO"],
    "pa system": ["SPEAKER-PA-PRO"],
    "pa systems": ["SPEAKER-PA-PRO"],
    "sound system": ["SPEAKER-PA-PRO"],
    "sound systems": ["SPEAKER-PA-PRO"],
    "audio system": ["SPEAKER-PA-PRO"],
    "audio systems": ["SPEAKER-PA-PRO"],
    "pa": ["SPEAKER-PA-PRO"],
    "speaker": ["SPEAKER-PA-BASIC"],
    "speakers": ["SPEAKER-PA-BASIC"],

    # Audio/Visual - Microphones
    "wireless microphone": ["MIC-WIRELESS-HH"],
    "wireless microphones": ["MIC-WIRELESS-HH"],
    "wireless mic": ["MIC-WIRELESS-HH"],
    "wireless mics": ["MIC-WIRELESS-HH"],
    "handheld microphone": ["MIC-WIRELESS-HH"],
    "handheld microphones": ["MIC-WIRELESS-HH"],
    "handheld mic": ["MIC-WIRELESS-HH"],
    "handheld mics": ["MIC-WIRELESS-HH"],
    "microphone": ["MIC-WIRELESS-HH"],
    "microphones": ["MIC-WIRELESS-HH"],
    "mic": ["MIC-WIRELESS-HH"],
    "mics": ["MIC-WIRELESS-HH"],

    # Audio/Visual - Other
    "audio mixer": ["MIXER-8CH"],
    "audio mixers": ["MIXER-8CH"],
    "mixer": ["MIXER-8CH"],
    "mixers": ["MIXER-8CH"],
    "led uplight": ["LIGHT-UPLIGHT-LED"],
    "led uplights": ["LIGHT-UPLIGHT-LED"],
    "uplight": ["LIGHT-UPLIGHT-LED"],
    "uplights": ["LIGHT-UPLIGHT-LED"],
    "led light": ["LIGHT-UPLIGHT-LED"],
    "led lights": ["LIGHT-UPLIGHT-LED"],
    "light": ["LIGHT-UPLIGHT-LED"],
    "lights": ["LIGHT-UPLIGHT-LED"],
    "4k projector": ["PROJECTOR-4K"],
    "4k projectors": ["PROJECTOR-4K"],
    "projector": ["PROJECTOR-4K"],
    "projectors": ["PROJECTOR-4K"],
    "projection screen": ["SCREEN-PROJ-120"],
    "projection screens": ["SCREEN-PROJ-120"],
    "screen": ["SCREEN-PROJ-120"],
    "screens": ["SCREEN-PROJ-120"],

    # Construction - Lifts
    "19ft scissor lift": ["LIFT-SCISSOR-19"],
    "19ft scissor lifts": ["LIFT-SCISSOR-19"],
    "19 ft scissor lift": ["LIFT-SCISSOR-19"],
    "19 foot scissor lift": ["LIFT-SCISSOR-19"],
    "19ft lift": ["LIFT-SCISSOR-19"],
    "26ft scissor lift": ["LIFT-SCISSOR-26"],
    "26ft scissor lifts": ["LIFT-SCISSOR-26"],
    "26 ft scissor lift": ["LIFT-SCISSOR-26"],
    "26 foot scissor lift": ["LIFT-SCISSOR-26"],
    "26ft lift": ["LIFT-SCISSOR-26"],
    "scissor lift": ["LIFT-SCISSOR-19"],
    "scissor lifts": ["LIFT-SCISSOR-19"],
    "40ft boom lift": ["LIFT-BOOM-40"],
    "40ft boom lifts": ["LIFT-BOOM-40"],
    "boom lift": ["LIFT-BOOM-40"],
    "boom lifts": ["LIFT-BOOM-40"],
    "telescopic lift": ["LIFT-BOOM-40"],
    "telescopic lifts": ["LIFT-BOOM-40"],
    "lift": ["LIFT-SCISSOR-19"],
    "lifts": ["LIFT-SCISSOR-19"],

    # Construction - Generators
    "10kw diesel generator": ["GEN-10KW-DIESEL"],
    "10kw generator": ["GEN-10KW-DIESEL"],
    "diesel generator": ["GEN-10KW-DIESEL"],
    "diesel generators": ["GEN-10KW-DIESEL"],
    "5kw generator": ["GEN-5KW"],
    "portable generator": ["GEN-5KW"],
    "portable generators": ["GEN-5KW"],
    "generator": ["GEN-5KW"],
    "generators": ["GEN-5KW"],
    "gen": ["GEN-5KW"],

    # Construction - Other
    "air compressor": ["COMPRESSOR-185CFM"],
    "air compressors": ["COMPRESSOR-185CFM"],
    "compressor": ["COMPRESSOR-185CFM"],
    "compressors": ["COMPRESSOR-185CFM"],
    "scaffolding": ["SCAFFOLD-5x5x7"],
    "scaffold": ["SCAFFOLD-5x5x7"],
    "scaffolds": ["SCAFFOLD-5x5x7"],

    # Heavy Equipment
    "fork lift": ["FORKLIFT-5K"],
    "fork lifts": ["FORKLIFT-5K"],
    "forklift": ["FORKLIFT-5K"],
    "forklifts": ["FORKLIFT-5K"],
    "skid steer": ["SKIDSTEER-1800"],
    "skid steers": ["SKIDSTEER-1800"],
    "skidsteer": ["SKIDSTEER-1800"],
    "skidsteers": ["SKIDSTEER-1800"],
    "loader": ["SKIDSTEER-1800"],
    "loaders": ["SKIDSTEER-1800"],
    "mini excavator": ["EXCAVATOR-MINI"],
    "mini excavators": ["EXCAVATOR-MINI"],
    "excavator": ["EXCAVATOR-MINI"],
    "excavators": ["EXCAVATOR-MINI"],

    # Climate Control
    "propane heater": ["HEATER-PROPANE"],
    "propane heaters": ["HEATER-PROPANE"],
    "heater": ["HEATER-PROPANE"],
    "heaters": ["HEATER-PROPANE"],
    "drum fan": ["FAN-DRUM-36"],
    "drum fans": ["FAN-DRUM-36"],
    "fan": ["FAN-DRUM-36"],
    "fans": ["FAN-DRUM-36"],
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


def normalize_text(text: str) -> str:
    """
    Normalize text for better matching.
    - Converts "60-inch" -> "60 inch"
    - Converts '60"' -> "60 inch"
    - Converts "60in" -> "60 inch"
    - Lowercase and strip
    """
    text = text.lower().strip()

    # Normalize inch patterns: 60-inch, 60", 60in -> 60 inch
    text = re.sub(r'(\d+)["\u201d\u201c]', r'\1 inch', text)  # 60" -> 60 inch
    text = re.sub(r'(\d+)-inch', r'\1 inch', text)  # 60-inch -> 60 inch
    text = re.sub(r'(\d+)in\b', r'\1 inch', text)  # 60in -> 60 inch

    # Normalize foot patterns: 8-foot, 8ft -> 8 foot
    text = re.sub(r'(\d+)-foot', r'\1 foot', text)  # 8-foot -> 8 foot
    text = re.sub(r'(\d+)ft\b', r'\1 foot', text)  # 8ft -> 8 foot
    text = re.sub(r'(\d+)\s*ft\b', r'\1 foot', text)  # 8 ft -> 8 foot

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def parse_quantity(text: str) -> Optional[int]:
    """
    Parse quantity from text, handling various formats.
    Examples: "50", "5x", "qty 5", "ten", "a dozen", "hundred"
    """
    text_lower = text.lower().strip()

    # Handle "5x" format
    x_match = re.match(r'^(\d+)x$', text_lower)
    if x_match:
        return int(x_match.group(1))

    # Handle "qty 5" or "qty: 5" format
    qty_match = re.match(r'^qty[:\s]*(\d+)$', text_lower)
    if qty_match:
        return int(qty_match.group(1))

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


def find_matching_sku(item_text: str, min_similarity: float = 0.55) -> Tuple[Optional[str], float]:
    """
    Find the best matching SKU for an item description using exact and fuzzy matching.

    Strategy:
    1. Normalize the input text
    2. Try exact match with normalized text
    3. Try longest-substring match (prioritize more specific synonyms)
    4. Fall back to fuzzy matching

    Args:
        item_text: The item description from customer message
        min_similarity: Minimum similarity threshold (0.0 to 1.0)

    Returns:
        Tuple of (SKU, confidence_score) or (None, 0.0) if no match
    """
    item_normalized = normalize_text(item_text)

    # First try exact match with normalized text
    if item_normalized in ITEM_SYNONYMS:
        sku = ITEM_SYNONYMS[item_normalized][0]
        logger.debug(f"Exact match: '{item_text}' -> {sku}")
        return (sku, 1.0)

    # Try to find the longest matching synonym (most specific)
    # Sort synonyms by length descending to prioritize longer/more specific matches
    sorted_synonyms = sorted(ITEM_SYNONYMS.keys(), key=len, reverse=True)

    for synonym in sorted_synonyms:
        synonym_normalized = normalize_text(synonym)
        # Check if the synonym is contained in the item text
        if synonym_normalized in item_normalized:
            sku = ITEM_SYNONYMS[synonym][0]
            # Higher confidence for longer matches
            confidence = min(1.0, 0.85 + (len(synonym) / 50))
            logger.debug(f"Substring match: '{item_text}' contains '{synonym}' -> {sku}")
            return (sku, confidence)

    # Try fuzzy matching against all synonyms
    best_match = None
    best_score = 0.0

    for synonym, skus in ITEM_SYNONYMS.items():
        score = similarity(item_normalized, normalize_text(synonym))
        if score > best_score and score >= min_similarity:
            best_score = score
            best_match = skus[0]

    if best_match:
        logger.debug(f"Fuzzy match: '{item_text}' -> {best_match} (score: {best_score:.2f})")
    else:
        logger.debug(f"No match found for: '{item_text}' (best score: {best_score:.2f})")

    return (best_match, best_score)


def extract_line_items(text: str) -> List[Dict[str, Any]]:
    """
    Extract line items from natural language text.

    This is the main normalization step that converts free-form text into
    structured line items with quantity, normalized name, and attributes.

    Handles:
    - "50 white folding chairs" -> {qty: 50, name: "white folding chairs"}
    - "5 60-inch round tables" -> {qty: 5, name: "60 inch round tables"}
    - "5x chairs" -> {qty: 5, name: "chairs"}
    - "qty 10 speakers" -> {qty: 10, name: "speakers"}
    - "ten microphones" -> {qty: 10, name: "microphones"}
    - "Need 10 speakers" -> {qty: 10, name: "speakers"}

    Returns:
        List of dicts with 'qty', 'normalizedName', 'rawText', and 'attributes'
    """
    logger.info(f"Extracting line items from: {text[:100]}...")

    # Normalize the entire text first
    text_normalized = normalize_text(text)

    # Strip common prefix words that don't add meaning
    # (need, want, get, require, looking for, etc.)
    prefix_pattern = r'^(?:i\s+)?(?:need|want|require|looking\s+for|give\s+me|get\s+me|get|send|order)\s+'
    text_normalized = re.sub(prefix_pattern, '', text_normalized, flags=re.IGNORECASE)

    line_items = []

    # Split by common separators: "and", ",", ";"
    # But be careful not to split on "and" within item names
    segments = re.split(r'\s*(?:,|;)\s*|\s+and\s+', text_normalized)

    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue

        # Also strip prefix words from each segment
        segment = re.sub(prefix_pattern, '', segment, flags=re.IGNORECASE).strip()
        if not segment:
            continue

        item = _parse_single_segment(segment)
        if item:
            line_items.append(item)

    # If no items found from segments, try parsing the whole text
    if not line_items:
        item = _parse_single_segment(text_normalized)
        if item:
            line_items.append(item)

    logger.info(f"Extracted {len(line_items)} line items")
    return line_items


def _parse_single_segment(segment: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single segment to extract quantity and item name.

    Patterns handled:
    - "50 white folding chairs"
    - "5x chairs"
    - "qty 5 speakers"
    - "ten microphones"
    - "5 60 inch round tables" (number-number pattern)
    """
    segment = segment.strip()
    if not segment:
        return None

    qty = 1
    item_name = segment

    # Pattern 1: "qty N item" or "qty: N item"
    qty_prefix = re.match(r'^qty[:\s]*(\d+)\s+(.+)$', segment, re.IGNORECASE)
    if qty_prefix:
        qty = int(qty_prefix.group(1))
        item_name = qty_prefix.group(2).strip()
        return {"qty": qty, "normalizedName": item_name, "rawText": segment, "attributes": {}}

    # Pattern 2: "Nx item" (e.g., "5x chairs")
    nx_pattern = re.match(r'^(\d+)x\s+(.+)$', segment, re.IGNORECASE)
    if nx_pattern:
        qty = int(nx_pattern.group(1))
        item_name = nx_pattern.group(2).strip()
        return {"qty": qty, "normalizedName": item_name, "rawText": segment, "attributes": {}}

    # Pattern 3: "N size-spec item" (e.g., "5 60 inch round tables", "5 60-inch tables")
    # This handles the tricky case where there are two numbers
    size_pattern = re.match(r'^(\d+)\s+(\d+)\s*(inch|foot|ft|in)?\s*(.+)$', segment, re.IGNORECASE)
    if size_pattern:
        qty = int(size_pattern.group(1))
        size_num = size_pattern.group(2)
        size_unit = size_pattern.group(3) or "inch"
        rest = size_pattern.group(4).strip()
        # Normalize the size unit
        if size_unit.lower() in ["in"]:
            size_unit = "inch"
        elif size_unit.lower() in ["ft"]:
            size_unit = "foot"
        item_name = f"{size_num} {size_unit} {rest}"
        return {"qty": qty, "normalizedName": item_name, "rawText": segment, "attributes": {"size": f"{size_num}{size_unit}"}}

    # Pattern 4: "N item" where N is a number (e.g., "50 chairs")
    num_pattern = re.match(r'^(\d+)\s+(.+)$', segment)
    if num_pattern:
        qty = int(num_pattern.group(1))
        item_name = num_pattern.group(2).strip()
        return {"qty": qty, "normalizedName": item_name, "rawText": segment, "attributes": {}}

    # Pattern 5: "a/an WORD_NUMBER item" (e.g., "a dozen tables", "a hundred chairs")
    # MUST come before simple word number pattern to avoid "a" being treated as qty 1
    compound_pattern = r'^(a|an)\s+(' + '|'.join(k for k in WORD_NUMBERS.keys() if k not in ['a', 'an']) + r')\s+(.+)$'
    compound_match = re.match(compound_pattern, segment, re.IGNORECASE)
    if compound_match:
        qty = WORD_NUMBERS.get(compound_match.group(2).lower(), 1)
        item_name = compound_match.group(3).strip()
        return {"qty": qty, "normalizedName": item_name, "rawText": segment, "attributes": {}}

    # Pattern 6: Word number + item (e.g., "ten speakers", "five chairs")
    word_num_pattern = r'^(' + '|'.join(WORD_NUMBERS.keys()) + r')\s+(.+)$'
    word_match = re.match(word_num_pattern, segment, re.IGNORECASE)
    if word_match:
        qty = WORD_NUMBERS.get(word_match.group(1).lower(), 1)
        item_name = word_match.group(2).strip()
        return {"qty": qty, "normalizedName": item_name, "rawText": segment, "attributes": {}}

    # No quantity found, assume 1
    return {"qty": 1, "normalizedName": item_name, "rawText": segment, "attributes": {}}


def parse_items_from_message(message: str) -> List[Dict[str, Any]]:
    """
    Parse rental items and quantities from a customer message.

    This is the main entry point for parsing customer requests.
    Uses a two-step process:
    1. Extract line items (qty + normalized name) from text
    2. Match each line item to a SKU with confidence scoring

    Handles patterns like:
    - "50 white folding chairs and 5 60-inch round tables"
    - "ten speakers and a mixer"
    - "need 20 uplights for corporate event"
    - "5x tables, 100 chairs"

    Args:
        message: Customer's free-text request

    Returns:
        List of dicts with 'sku', 'quantity', 'confidence', and 'source' keys.
        Items that couldn't be matched have sku=None and are flagged as unmatched.
    """
    logger.info(f"Parsing items from message: {message[:100]}...")

    # Step 1: Extract line items
    line_items = extract_line_items(message)

    # Step 2: Match each line item to SKU
    items = []
    for line_item in line_items:
        qty = line_item["qty"]
        name = line_item["normalizedName"]

        sku, confidence = find_matching_sku(name)

        if sku:
            items.append({
                "sku": sku,
                "quantity": qty,
                "confidence": confidence,
                "source": line_item["rawText"],
                "matched": True
            })
        else:
            # Return unmatched item for transparency
            items.append({
                "sku": None,
                "quantity": qty,
                "confidence": 0.0,
                "source": line_item["rawText"],
                "matched": False,
                "unmatched_name": name
            })

    # Remove duplicates (same SKU), keeping the one with highest confidence
    seen_skus = {}
    unique_items = []
    for item in items:
        sku = item["sku"]
        if sku is None:
            unique_items.append(item)
        elif sku not in seen_skus:
            seen_skus[sku] = len(unique_items)
            unique_items.append(item)
        else:
            # If we've seen this SKU, keep the one with higher confidence/quantity
            existing_idx = seen_skus[sku]
            if item["confidence"] > unique_items[existing_idx]["confidence"]:
                unique_items[existing_idx] = item

    logger.info(
        f"Parsed {len(unique_items)} items from message",
        extra={"extra_fields": {
            "item_count": len(unique_items),
            "items": [{"sku": i["sku"], "qty": i["quantity"], "conf": i["confidence"], "matched": i.get("matched", True)} for i in unique_items]
        }}
    )

    return unique_items


def extract_duration_hint(message: str) -> Optional[int]:
    """
    Try to extract rental duration from message text.

    Examples:
    - "for 3 days" -> 3
    - "5 day rental" -> 5
    - "weekend" -> 3 (Fri-Sun)
    - "friday through sunday" -> 3
    - "week" -> 7

    Returns:
        Number of days or None if not found
    """
    message_lower = message.lower()

    # Pattern: "for N days" or "N day rental"
    day_match = re.search(r'\b(\d+)\s*days?\b', message_lower)
    if day_match:
        return int(day_match.group(1))

    # Pattern: "friday through sunday" or similar
    if re.search(r'friday\s+(?:through|thru|to|-)\s+sunday', message_lower):
        return 3

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
