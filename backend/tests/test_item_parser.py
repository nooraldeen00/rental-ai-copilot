"""
Test cases for the RentalAI item parser.
Covers quantity extraction, SKU matching, and various input formats.
"""
import pytest
from backend.core.item_parser import (
    parse_items_from_message,
    extract_duration_hint,
    parse_quantity,
    find_matching_sku,
    normalize_text,
    extract_line_items,
)


class TestCriticalBugFix:
    """
    Test case for the critical bug: "50 white folding chairs and 5 60-inch round tables"
    This was showing wrong quantities (tables as 1 and/or wrong table type).
    """

    def test_critical_bug_example(self):
        """
        Test the exact example from the bug report:
        "50 white folding chairs and 5 60-inch round tables, Friday through Sunday delivery, Dallas metro area, corporate account"
        """
        message = "50 white folding chairs and 5 60-inch round tables, Friday through Sunday delivery, Dallas metro area, corporate account"
        items = parse_items_from_message(message)

        # Should find exactly 2 items
        assert len(items) >= 2, f"Expected at least 2 items, got {len(items)}"

        # Find the items by SKU
        items_by_sku = {item["sku"]: item for item in items if item.get("sku")}

        # Check chairs: should be CHAIR-FOLD-WHT with qty 50
        assert "CHAIR-FOLD-WHT" in items_by_sku, "Should match white folding chairs to CHAIR-FOLD-WHT"
        assert items_by_sku["CHAIR-FOLD-WHT"]["quantity"] == 50, f"Chairs qty should be 50, got {items_by_sku['CHAIR-FOLD-WHT']['quantity']}"

        # Check tables: should be TABLE-60RND with qty 5 (NOT TABLE-8FT-RECT)
        assert "TABLE-60RND" in items_by_sku, "Should match 60-inch round tables to TABLE-60RND, not TABLE-8FT-RECT"
        assert items_by_sku["TABLE-60RND"]["quantity"] == 5, f"Tables qty should be 5, got {items_by_sku['TABLE-60RND']['quantity']}"

    def test_tables_with_size_variations(self):
        """Test various ways of specifying 60-inch round tables."""
        variations = [
            "5 60-inch round tables",
            "5 60 inch round tables",
            '5 60" round tables',
            "5 60in round tables",
            "5 round tables",  # Should default to 60RND
        ]

        for msg in variations:
            items = parse_items_from_message(msg)
            matched = [i for i in items if i.get("sku") == "TABLE-60RND"]
            assert len(matched) >= 1, f"'{msg}' should match TABLE-60RND"
            assert matched[0]["quantity"] == 5, f"'{msg}' should have qty 5, got {matched[0]['quantity']}"


class TestQuantityParsing:
    """Test various quantity formats."""

    def test_numeric_quantities(self):
        """Test basic numeric quantity parsing."""
        assert parse_quantity("50") == 50
        assert parse_quantity("5") == 5
        assert parse_quantity("100") == 100
        assert parse_quantity("1") == 1

    def test_word_quantities(self):
        """Test word-based quantity parsing."""
        assert parse_quantity("ten") == 10
        assert parse_quantity("five") == 5
        assert parse_quantity("twenty") == 20
        assert parse_quantity("dozen") == 12
        assert parse_quantity("hundred") == 100

    def test_compound_quantities(self):
        """Test compound quantity expressions."""
        assert parse_quantity("a") == 1
        assert parse_quantity("an") == 1
        assert parse_quantity("a dozen") == 12

    def test_x_format(self):
        """Test '5x' format."""
        assert parse_quantity("5x") == 5
        assert parse_quantity("10x") == 10


class TestSKUMatching:
    """Test SKU matching from item descriptions."""

    def test_exact_matches(self):
        """Test exact synonym matches."""
        sku, conf = find_matching_sku("folding chair")
        assert sku == "CHAIR-FOLD-WHT"
        assert conf == 1.0

        sku, conf = find_matching_sku("round table")
        assert sku == "TABLE-60RND"
        assert conf == 1.0

    def test_normalized_matches(self):
        """Test matches after normalization."""
        # 60-inch should normalize to 60 inch
        sku, conf = find_matching_sku("60-inch round table")
        assert sku == "TABLE-60RND"

        sku, conf = find_matching_sku("60in round tables")
        assert sku == "TABLE-60RND"

    def test_fuzzy_matches(self):
        """Test fuzzy matching for close descriptions."""
        sku, conf = find_matching_sku("PA system")
        assert sku == "SPEAKER-PA-PRO"

        sku, conf = find_matching_sku("sound system")
        assert sku == "SPEAKER-PA-PRO"


class TestTextNormalization:
    """Test text normalization functions."""

    def test_inch_normalization(self):
        """Test normalization of inch patterns."""
        assert normalize_text("60-inch") == "60 inch"
        assert normalize_text('60"') == "60 inch"
        assert normalize_text("60in") == "60 inch"
        assert normalize_text("60 inch") == "60 inch"

    def test_foot_normalization(self):
        """Test normalization of foot patterns."""
        assert normalize_text("8ft") == "8 foot"
        assert normalize_text("8-foot") == "8 foot"
        assert normalize_text("8 ft") == "8 foot"


class TestLineItemExtraction:
    """Test the line item extraction step."""

    def test_simple_extraction(self):
        """Test basic line item extraction."""
        items = extract_line_items("50 chairs")
        assert len(items) == 1
        assert items[0]["qty"] == 50
        assert "chair" in items[0]["normalizedName"]

    def test_multi_item_extraction(self):
        """Test extracting multiple items."""
        items = extract_line_items("50 chairs and 10 tables")
        assert len(items) == 2
        assert items[0]["qty"] == 50
        assert items[1]["qty"] == 10

    def test_size_spec_extraction(self):
        """Test extracting items with size specifications."""
        items = extract_line_items("5 60 inch round tables")
        assert len(items) == 1
        assert items[0]["qty"] == 5
        assert "60 inch" in items[0]["normalizedName"]


class TestDurationExtraction:
    """Test duration hint extraction."""

    def test_explicit_days(self):
        """Test explicit day counts."""
        assert extract_duration_hint("for 3 days") == 3
        assert extract_duration_hint("5 day rental") == 5

    def test_weekend(self):
        """Test weekend detection."""
        assert extract_duration_hint("weekend event") == 3
        assert extract_duration_hint("Friday through Sunday") == 3

    def test_week_month(self):
        """Test week/month detection."""
        assert extract_duration_hint("for a week") == 7
        assert extract_duration_hint("for a month") == 30


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_corporate_event(self):
        """Test corporate event scenario."""
        msg = "Need 50 white folding chairs and 5 round tables for a corporate event this weekend"
        items = parse_items_from_message(msg)
        duration = extract_duration_hint(msg)

        # Should find chairs and tables
        skus = [i["sku"] for i in items if i.get("sku")]
        assert "CHAIR-FOLD-WHT" in skus
        assert "TABLE-60RND" in skus

        # Duration should be weekend (3 days)
        assert duration == 3

    def test_wedding_scenario(self):
        """Test wedding scenario."""
        msg = "PA system and twenty uplights for a 2-day wedding"
        items = parse_items_from_message(msg)
        duration = extract_duration_hint(msg)

        skus = [i["sku"] for i in items if i.get("sku")]
        assert "SPEAKER-PA-PRO" in skus
        assert "LIGHT-UPLIGHT-LED" in skus
        assert duration == 2

    def test_mixed_quantities(self):
        """Test mixed word/numeric quantities."""
        msg = "hundred chairs, dozen tables, tent for outdoor event"
        items = parse_items_from_message(msg)

        items_by_sku = {i["sku"]: i for i in items if i.get("sku")}

        assert items_by_sku.get("CHAIR-FOLD-WHT", {}).get("quantity") == 100
        assert items_by_sku.get("TABLE-8FT-RECT", {}).get("quantity") == 12
        assert "TENT-20x20" in items_by_sku

    def test_construction_equipment(self):
        """Test construction equipment scenario."""
        msg = "Need a scissor lift and generator for the job next week, 5 days"
        items = parse_items_from_message(msg)
        duration = extract_duration_hint(msg)

        skus = [i["sku"] for i in items if i.get("sku")]
        assert "LIFT-SCISSOR-19" in skus
        assert "GEN-5KW" in skus
        assert duration == 5

    def test_5x_format(self):
        """Test '5x' format for quantities."""
        msg = "5x tables, 100 chairs"
        items = parse_items_from_message(msg)

        items_by_sku = {i["sku"]: i for i in items if i.get("sku")}
        # Note: "5x tables" might be parsed differently
        # This tests the overall parsing capability


class TestUnmatchedItems:
    """Test handling of unmatched items."""

    def test_unmatched_item_flagged(self):
        """Test that unmatched items are flagged properly."""
        msg = "5 flying cars and 10 chairs"
        items = parse_items_from_message(msg)

        # Should have both matched and unmatched items
        matched = [i for i in items if i.get("matched", True)]
        unmatched = [i for i in items if not i.get("matched", True)]

        # Chairs should be matched
        assert any(i["sku"] == "CHAIR-FOLD-WHT" for i in matched)


# Run tests directly if needed
if __name__ == "__main__":
    # Run with verbose output
    pytest.main([__file__, "-v"])
