"""
Test cases for improved item parser
Demonstrates the parsing capabilities with various input messages
"""
from backend.core.item_parser import parse_items_from_message, extract_duration_hint, parse_quantity


def test_example_scenarios():
    """
    Test the 5 example scenarios from the improvement proposal
    """
    print("=" * 80)
    print("ITEM PARSER TEST SCENARIOS")
    print("=" * 80)

    scenarios = [
        {
            "num": 1,
            "message": "Need 50 white folding chairs and 5 round tables for a corporate event this weekend",
            "expected_items": ["50x CHAIR-FOLD-WHT", "5x TABLE-60RND"],
            "expected_duration": 3,
        },
        {
            "num": 2,
            "message": "Ten speakers and a mixer for Friday through Sunday",
            "expected_items": ["10x SPEAKER-PA-BASIC", "1x MIXER-8CH"],
            "expected_duration": 3,
        },
        {
            "num": 3,
            "message": "PA system and twenty uplights for a 2-day wedding",
            "expected_items": ["1x SPEAKER-PA-PRO", "20x LIGHT-UPLIGHT-LED"],
            "expected_duration": 2,
        },
        {
            "num": 4,
            "message": "Need a scissor lift and generator for the job next week, 5 days",
            "expected_items": ["1x LIFT-SCISSOR-19", "1x GEN-5KW"],
            "expected_duration": 5,
        },
        {
            "num": 5,
            "message": "hundred chairs, dozen tables, tent for outdoor event",
            "expected_items": ["100x CHAIR-FOLD-WHT", "12x TABLE-8FT-RECT", "1x TENT-20x20"],
            "expected_duration": None,
        },
    ]

    for scenario in scenarios:
        print(f"\n{'─' * 80}")
        print(f"SCENARIO #{scenario['num']}")
        print(f"{'─' * 80}")
        print(f"Message: \"{scenario['message']}\"")
        print()

        # Parse items
        items = parse_items_from_message(scenario['message'])
        print(f"✓ Parsed {len(items)} items:")
        for item in items:
            print(f"  - {item['quantity']}x {item['sku']} (confidence: {item['confidence']:.2f}, source: {item['source']})")

        # Extract duration
        duration = extract_duration_hint(scenario['message'])
        if duration:
            print(f"\n✓ Extracted duration: {duration} days")
        else:
            print(f"\n  (No duration hint found, will use fallback)")

        print(f"\nExpected items: {', '.join(scenario['expected_items'])}")
        if scenario['expected_duration']:
            print(f"Expected duration: {scenario['expected_duration']} days")

    print(f"\n{'=' * 80}\n")


def test_quantity_parsing():
    """Test word-based quantity parsing"""
    print("=" * 80)
    print("QUANTITY PARSING TESTS")
    print("=" * 80)

    test_cases = [
        ("50", 50),
        ("ten", 10),
        ("a dozen", 12),
        ("dozen", 12),
        ("hundred", 100),
        ("twenty", 20),
        ("a", 1),
        ("one", 1),
        ("5", 5),
    ]

    for text, expected in test_cases:
        result = parse_quantity(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' → {result} (expected: {expected})")

    print(f"\n{'=' * 80}\n")


def test_fuzzy_matching():
    """Test fuzzy matching for various equipment descriptions"""
    print("=" * 80)
    print("FUZZY MATCHING TESTS")
    print("=" * 80)

    test_messages = [
        "Need sound system for event",  # Should match PA system
        "Looking for audio mixer and mics",  # Should match mixer and microphones
        "Require boom lift for construction",  # Should match boom lift
        "Get me some uplights and a projector",  # Should match uplights and projector
        "Need portable generator",  # Should match generator
        "Want chiavari chairs for wedding",  # Should match chiavari chairs
    ]

    for msg in test_messages:
        items = parse_items_from_message(msg)
        print(f"\nMessage: \"{msg}\"")
        if items:
            print(f"  Matched:")
            for item in items:
                print(f"    - {item['sku']} (qty: {item['quantity']}, conf: {item['confidence']:.2f})")
        else:
            print(f"  No matches found")

    print(f"\n{'=' * 80}\n")


if __name__ == "__main__":
    test_example_scenarios()
    test_quantity_parsing()
    test_fuzzy_matching()
    print("All tests completed!")
