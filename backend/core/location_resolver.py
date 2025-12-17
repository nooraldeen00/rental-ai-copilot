# backend/core/location_resolver.py
"""
Location Resolution and Reconciliation Module

This module provides the LocationResolver class which serves as the single source
of truth for resolving locations from multiple input sources:
1. Free-text location from customer request
2. Selected service location from dropdown
3. Postal code

The resolver determines the final canonical location for pricing/fees and
detects conflicts between the sources.
"""

from __future__ import annotations
import re
from typing import Optional, Dict, Any, List, Tuple
from difflib import SequenceMatcher

from backend.core.logging_config import get_logger
from backend.models import ResolvedLocation, ServiceLocationMeta

logger = get_logger(__name__)

# Known service locations for normalization
KNOWN_LOCATIONS: Dict[str, List[str]] = {
    "Dallas, TX": ["dallas", "dallas tx", "dallas, tx", "dallas metro", "dallas area", "dallas metro area"],
    "Fort Worth, TX": ["fort worth", "fort worth tx", "fort worth, tx", "ft worth", "ft. worth", "fortworth"],
    "Plano, TX": ["plano", "plano tx", "plano, tx"],
    "Arlington, TX": ["arlington", "arlington tx", "arlington, tx"],
    "Southlake, TX": ["southlake", "southlake tx", "southlake, tx"],
}

# Location keywords/patterns to extract from free text
LOCATION_PATTERNS = [
    r'\b(dallas|fort\s*worth|plano|arlington|southlake)(?:\s*,?\s*(?:tx|texas))?\b',
    r'\b(austin|houston|san\s*antonio)(?:\s*,?\s*(?:tx|texas))?\b',
    r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?)\b',
    r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?)\b',
    r'\bnear\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?(?:,\s*[A-Z]{2})?)\b',
]


class LocationResolver:
    """
    Resolves and reconciles location from multiple sources.

    This is the single source of truth for location resolution, used by both
    fee calculation and AI notes prompt builder.
    """

    def __init__(self, similarity_threshold: float = 0.6):
        """
        Initialize the LocationResolver.

        Args:
            similarity_threshold: Minimum string similarity (0-1) to consider
                                  two locations as matching. Default 0.6.
        """
        self.similarity_threshold = similarity_threshold

    def resolve(
        self,
        request_text: Optional[str] = None,
        selected_location_id: Optional[str] = None,
        selected_location_label: Optional[str] = None,
        selected_location_meta: Optional[Dict[str, Any]] = None,
        postal_code: Optional[str] = None,
    ) -> ResolvedLocation:
        """
        Resolve location from multiple input sources.

        Args:
            request_text: Customer's free-text request message
            selected_location_id: ID of selected service location
            selected_location_label: Display label of selected location
            selected_location_meta: Zone/region metadata for selected location
            postal_code: Optional postal/ZIP code

        Returns:
            ResolvedLocation with all location fields and conflict detection
        """
        logger.debug(
            "Resolving location",
            extra={"extra_fields": {
                "has_request_text": bool(request_text),
                "selected_location_id": selected_location_id,
                "selected_location_label": selected_location_label,
                "postal_code": postal_code,
            }}
        )

        # Extract location from free text
        free_text_location = self._extract_location_from_text(request_text) if request_text else None

        # Build selected location metadata
        selected_meta = None
        if selected_location_meta:
            selected_meta = ServiceLocationMeta(
                zone=selected_location_meta.get("zone"),
                region=selected_location_meta.get("region")
            )

        # Determine final location and detect conflicts
        final_location, conflict, conflict_message, rationale = self._determine_final_location(
            free_text=free_text_location,
            selected_label=selected_location_label,
            postal_code=postal_code
        )

        result = ResolvedLocation(
            location_free_text=free_text_location,
            location_selected=selected_location_label,
            location_selected_id=selected_location_id,
            location_selected_meta=selected_meta,
            location_final=final_location,
            location_conflict=conflict,
            conflict_message=conflict_message,
            rationale=rationale
        )

        logger.info(
            f"Location resolved: final='{final_location}', conflict={conflict}",
            extra={"extra_fields": {
                "free_text": free_text_location,
                "selected": selected_location_label,
                "final": final_location,
                "conflict": conflict,
            }}
        )

        return result

    def _extract_location_from_text(self, text: str) -> Optional[str]:
        """
        Extract location mentions from free-text request.

        Args:
            text: Customer's free-text request

        Returns:
            Extracted location phrase, or None if not found
        """
        if not text:
            return None

        text_lower = text.lower()

        # First, check for known location keywords
        for canonical, aliases in KNOWN_LOCATIONS.items():
            for alias in aliases:
                if alias in text_lower:
                    logger.debug(f"Found known location '{canonical}' via alias '{alias}'")
                    return canonical

        # Try regex patterns for other locations
        for pattern in LOCATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Normalize common variations
                location = self._normalize_location(location)
                if location:
                    logger.debug(f"Extracted location via pattern: '{location}'")
                    return location

        return None

    def _normalize_location(self, location: str) -> str:
        """Normalize a location string to canonical form."""
        if not location:
            return location

        location_lower = location.lower().strip()

        # Check against known locations
        for canonical, aliases in KNOWN_LOCATIONS.items():
            if location_lower in aliases or canonical.lower() == location_lower:
                return canonical

        # Return title-cased version
        return location.title()

    def _determine_final_location(
        self,
        free_text: Optional[str],
        selected_label: Optional[str],
        postal_code: Optional[str]
    ) -> Tuple[str, bool, Optional[str], str]:
        """
        Determine the final canonical location and detect conflicts.

        Returns:
            Tuple of (final_location, has_conflict, conflict_message, rationale)
        """
        # Case 1: Selected location exists - it takes precedence for pricing
        if selected_label:
            if free_text:
                # Both exist - check for conflict
                conflict = not self._locations_match(free_text, selected_label)
                if conflict:
                    conflict_message = (
                        f"Location mismatch: customer wrote '{free_text}' but selected "
                        f"'{selected_label}'. Using selected location for pricing."
                    )
                    rationale = (
                        f"Selected service location '{selected_label}' used for pricing. "
                        f"Customer mentioned '{free_text}' in their request - please confirm."
                    )
                else:
                    conflict_message = None
                    rationale = f"Service location '{selected_label}' confirmed by customer request."

                return selected_label, conflict, conflict_message, rationale
            else:
                # Only selected location
                return (
                    selected_label,
                    False,
                    None,
                    f"Service location '{selected_label}' selected by customer."
                )

        # Case 2: No selection, but free text exists
        if free_text:
            return (
                free_text,
                False,
                None,
                f"Location '{free_text}' identified from customer request."
            )

        # Case 3: Only postal code
        if postal_code:
            return (
                f"ZIP {postal_code}",
                False,
                None,
                f"Location based on postal code {postal_code}."
            )

        # Case 4: Nothing provided
        return (
            "Unknown / Not provided",
            False,
            None,
            "No specific location provided. Default service area assumed."
        )

    def _locations_match(self, location1: str, location2: str) -> bool:
        """
        Check if two location strings refer to the same place.

        Uses string similarity and known alias matching.
        """
        if not location1 or not location2:
            return False

        # Normalize both locations
        loc1_lower = location1.lower().strip()
        loc2_lower = location2.lower().strip()

        # Exact match (case-insensitive)
        if loc1_lower == loc2_lower:
            return True

        # Check if either is contained in the other
        if loc1_lower in loc2_lower or loc2_lower in loc1_lower:
            return True

        # Check known aliases
        loc1_canonical = self._get_canonical_location(loc1_lower)
        loc2_canonical = self._get_canonical_location(loc2_lower)

        if loc1_canonical and loc2_canonical:
            if loc1_canonical == loc2_canonical:
                return True

        # Fuzzy string matching
        similarity = SequenceMatcher(None, loc1_lower, loc2_lower).ratio()
        if similarity >= self.similarity_threshold:
            return True

        # Check city name overlap (e.g., "Dallas metro area" vs "Dallas, TX")
        loc1_parts = set(re.findall(r'\b\w+\b', loc1_lower))
        loc2_parts = set(re.findall(r'\b\w+\b', loc2_lower))

        # Remove common words
        common_words = {'tx', 'texas', 'metro', 'area', 'downtown', 'north', 'south', 'east', 'west'}
        loc1_meaningful = loc1_parts - common_words
        loc2_meaningful = loc2_parts - common_words

        # If meaningful words overlap significantly
        if loc1_meaningful and loc2_meaningful:
            overlap = loc1_meaningful & loc2_meaningful
            if overlap:
                return True

        return False

    def _get_canonical_location(self, location_lower: str) -> Optional[str]:
        """Get canonical location name from a lowercase location string."""
        for canonical, aliases in KNOWN_LOCATIONS.items():
            if location_lower in aliases or canonical.lower() == location_lower:
                return canonical
        return None


# Module-level resolver instance for convenience
_resolver = LocationResolver()


def resolve_location(
    request_text: Optional[str] = None,
    selected_location_id: Optional[str] = None,
    selected_location_label: Optional[str] = None,
    selected_location_meta: Optional[Dict[str, Any]] = None,
    postal_code: Optional[str] = None,
) -> ResolvedLocation:
    """
    Convenience function to resolve location using the default resolver.

    This is the recommended way to resolve locations - use this function
    rather than instantiating LocationResolver directly.
    """
    return _resolver.resolve(
        request_text=request_text,
        selected_location_id=selected_location_id,
        selected_location_label=selected_location_label,
        selected_location_meta=selected_location_meta,
        postal_code=postal_code
    )
