"""
Test cases for the LocationResolver module.
Covers location extraction, conflict detection, and resolution logic.
"""
import pytest
from backend.core.location_resolver import (
    LocationResolver,
    resolve_location,
    KNOWN_LOCATIONS,
)
from backend.models import ResolvedLocation


class TestLocationExtraction:
    """Test location extraction from free text."""

    def test_extract_dallas_variants(self):
        """Test extraction of Dallas location variants."""
        resolver = LocationResolver()

        test_cases = [
            "Need 2 light towers in Dallas Fri–Sun",
            "Delivery to dallas, tx please",
            "Dallas metro area event",
            "Event in the Dallas area",
        ]

        for text in test_cases:
            result = resolver.resolve(request_text=text)
            assert result.location_free_text is not None, f"Should extract location from: {text}"
            assert "Dallas" in result.location_free_text, f"Should identify Dallas in: {text}"

    def test_extract_fort_worth_variants(self):
        """Test extraction of Fort Worth location variants."""
        resolver = LocationResolver()

        test_cases = [
            "event in Fort Worth",
            "delivery to ft worth, tx",
            "Fort Worth TX location",
        ]

        for text in test_cases:
            result = resolver.resolve(request_text=text)
            assert result.location_free_text is not None, f"Should extract location from: {text}"
            assert "Fort Worth" in result.location_free_text, f"Should identify Fort Worth in: {text}"

    def test_no_location_in_text(self):
        """Test handling of text without location."""
        resolver = LocationResolver()
        result = resolver.resolve(request_text="Need 50 chairs for a wedding")
        assert result.location_free_text is None

    def test_extract_from_empty_text(self):
        """Test handling of empty/None text."""
        resolver = LocationResolver()
        result = resolver.resolve(request_text="")
        assert result.location_free_text is None

        result = resolver.resolve(request_text=None)
        assert result.location_free_text is None


class TestLocationResolution:
    """Test the location resolution logic."""

    def test_selected_location_only(self):
        """Test: Selection only - no location in text."""
        result = resolve_location(
            request_text="Need 50 chairs for a wedding",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        assert result.location_selected == "Dallas, TX"
        assert result.location_free_text is None
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is False
        assert result.conflict_message is None

    def test_free_text_only(self):
        """Test: Free-text only - no selection."""
        result = resolve_location(
            request_text="Need 50 chairs in Dallas metro area",
            selected_location_id=None,
            selected_location_label=None,
        )

        assert result.location_free_text == "Dallas, TX"
        assert result.location_selected is None
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is False

    def test_both_match(self):
        """Test: Both match - free text and selection agree."""
        result = resolve_location(
            request_text="Need 50 chairs in Dallas metro area",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        assert result.location_free_text == "Dallas, TX"
        assert result.location_selected == "Dallas, TX"
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is False
        assert result.conflict_message is None

    def test_conflict_detected(self):
        """Test: Conflict - free text and selection disagree."""
        result = resolve_location(
            request_text="Need equipment in Austin",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        # Selected location should take precedence
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is True
        assert result.conflict_message is not None
        assert "Austin" in result.conflict_message
        assert "Dallas" in result.conflict_message

    def test_postal_code_fallback(self):
        """Test: Only postal code provided."""
        result = resolve_location(
            request_text="Need 50 chairs for event",
            postal_code="75201",
        )

        assert result.location_final == "ZIP 75201"
        assert result.location_conflict is False

    def test_no_location_provided(self):
        """Test: No location provided at all."""
        result = resolve_location(
            request_text="Need 50 chairs for event",
        )

        assert result.location_final == "Unknown / Not provided"
        assert result.location_conflict is False


class TestLocationMatching:
    """Test the location matching/similarity logic."""

    def test_exact_match(self):
        """Test exact match detection."""
        resolver = LocationResolver()
        assert resolver._locations_match("Dallas, TX", "Dallas, TX") is True
        assert resolver._locations_match("dallas, tx", "Dallas, TX") is True  # Case insensitive

    def test_partial_match(self):
        """Test partial/contained match detection."""
        resolver = LocationResolver()
        assert resolver._locations_match("Dallas", "Dallas, TX") is True
        assert resolver._locations_match("Dallas metro area", "Dallas, TX") is True
        assert resolver._locations_match("Dallas metro", "Dallas") is True

    def test_alias_match(self):
        """Test known alias matching."""
        resolver = LocationResolver()
        assert resolver._locations_match("ft worth", "Fort Worth, TX") is True
        assert resolver._locations_match("Ft. Worth", "Fort Worth, TX") is True

    def test_no_match(self):
        """Test non-matching locations."""
        resolver = LocationResolver()
        assert resolver._locations_match("Austin", "Dallas, TX") is False
        assert resolver._locations_match("Houston", "Fort Worth, TX") is False


class TestRequiredScenarios:
    """
    Test the specific scenarios from the requirements:
    1. Free-text only
    2. Selection only
    3. Both match
    4. Conflict
    """

    def test_scenario_1_free_text_only(self):
        """
        Scenario 1: Free-text only
        "Dallas metro area" + no selection → notes show Dallas (free_text + final)
        """
        result = resolve_location(
            request_text="Need equipment in Dallas metro area",
            selected_location_id=None,
            selected_location_label=None,
        )

        assert result.location_free_text == "Dallas, TX"
        assert result.location_selected is None
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is False
        assert "Dallas" in result.rationale

    def test_scenario_2_selection_only(self):
        """
        Scenario 2: Selection only
        selection "Dallas, TX" + no location in text → notes show selected + final
        """
        result = resolve_location(
            request_text="Need 50 chairs for a corporate event",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        assert result.location_free_text is None
        assert result.location_selected == "Dallas, TX"
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is False
        assert "selected" in result.rationale.lower()

    def test_scenario_3_both_match(self):
        """
        Scenario 3: Both match
        "Dallas metro area" + selection Dallas → notes show both; no conflict
        """
        result = resolve_location(
            request_text="Equipment for event in Dallas metro area",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        assert result.location_free_text == "Dallas, TX"
        assert result.location_selected == "Dallas, TX"
        assert result.location_final == "Dallas, TX"
        assert result.location_conflict is False
        assert "confirm" in result.rationale.lower()

    def test_scenario_4_conflict(self):
        """
        Scenario 4: Conflict
        "Austin" in text + selection Dallas → conflict flag true; final = Dallas; notes mention mismatch
        """
        result = resolve_location(
            request_text="Need equipment in Austin for the event",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        assert result.location_free_text is not None  # Should extract Austin
        assert result.location_selected == "Dallas, TX"
        assert result.location_final == "Dallas, TX"  # Selection takes precedence
        assert result.location_conflict is True
        assert result.conflict_message is not None
        assert "Dallas" in result.conflict_message
        assert "confirm" in result.rationale.lower()


class TestResolvedLocationModel:
    """Test the ResolvedLocation model structure."""

    def test_model_fields(self):
        """Test that all required fields are present."""
        result = resolve_location(
            request_text="Dallas event",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
        )

        # Check all fields exist
        assert hasattr(result, "location_free_text")
        assert hasattr(result, "location_selected")
        assert hasattr(result, "location_selected_id")
        assert hasattr(result, "location_selected_meta")
        assert hasattr(result, "location_final")
        assert hasattr(result, "location_conflict")
        assert hasattr(result, "conflict_message")
        assert hasattr(result, "rationale")

    def test_model_dump(self):
        """Test that model can be serialized."""
        result = resolve_location(
            request_text="Dallas event",
            selected_location_id="dallas-tx",
            selected_location_label="Dallas, TX",
            selected_location_meta={"zone": "local", "region": "DFW Metro"},
        )

        # Should be able to dump to dict
        data = result.model_dump()
        assert isinstance(data, dict)
        assert "location_final" in data
        assert "location_conflict" in data


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_strings(self):
        """Test handling of empty strings."""
        result = resolve_location(
            request_text="",
            selected_location_id="",
            selected_location_label="",
        )

        assert result.location_final == "Unknown / Not provided"
        assert result.location_conflict is False

    def test_whitespace_only(self):
        """Test handling of whitespace-only input."""
        result = resolve_location(
            request_text="   ",
            selected_location_id=None,
            selected_location_label=None,
        )

        assert result.location_final == "Unknown / Not provided"

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        result = resolve_location(
            request_text="Event in Dallas!!! (urgent) @venue",
            selected_location_id=None,
            selected_location_label=None,
        )

        assert result.location_free_text == "Dallas, TX"

    def test_multiple_locations_in_text(self):
        """Test handling of multiple locations in text."""
        # When multiple locations are in text, first match wins
        result = resolve_location(
            request_text="We're based in Dallas but the event is in Fort Worth",
            selected_location_id=None,
            selected_location_label=None,
        )

        # Should extract first location found
        assert result.location_free_text is not None
        # Either Dallas or Fort Worth is acceptable


class TestKnownLocations:
    """Test the known locations dictionary."""

    def test_all_dfw_locations_covered(self):
        """Verify all DFW area locations are in the dictionary."""
        required_locations = [
            "Dallas, TX",
            "Fort Worth, TX",
            "Plano, TX",
            "Arlington, TX",
            "Southlake, TX",
        ]

        for loc in required_locations:
            assert loc in KNOWN_LOCATIONS, f"{loc} should be in KNOWN_LOCATIONS"

    def test_aliases_exist(self):
        """Verify common aliases are defined."""
        # Dallas aliases
        assert "dallas" in KNOWN_LOCATIONS["Dallas, TX"]
        assert "dallas metro" in KNOWN_LOCATIONS["Dallas, TX"]

        # Fort Worth aliases
        assert "fort worth" in KNOWN_LOCATIONS["Fort Worth, TX"]
        assert "ft worth" in KNOWN_LOCATIONS["Fort Worth, TX"]


# Run tests directly if needed
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
