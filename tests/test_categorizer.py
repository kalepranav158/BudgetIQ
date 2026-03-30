from backend.fastapi_service.parser.categorizer import (
    build_keyword_map,
    build_regex_rules,
    categorize_description,
    categorize_with_regex,
    extract_upi_counterparty_name,
)


def test_categorizer_uses_keyword_map() -> None:
    mappings = [
        {"keyword": "ZOMATO", "category": "lunch"},
        {"keyword": "ATM", "category": "cash_withdrawal"},
    ]

    keyword_map = build_keyword_map(mappings)

    assert categorize_description("UPI/ZOMATO ORDER", keyword_map) == "lunch"
    assert categorize_description("ATM CASH WD", keyword_map) == "cash_withdrawal"
    assert categorize_description("UNKNOWN MERCHANT", keyword_map) == "other"


def test_regex_mapping_overrides_keyword_and_sets_canonical_name() -> None:
    mappings = [
        {"kind": "keyword", "keyword": "UPI", "category": "other"},
        {
            "kind": "regex",
            "name": "Swiggy",
            "pattern": r"SWIGGY|BUNDL",
            "category": "lunch",
            "priority": 1,
        },
    ]

    keyword_map = build_keyword_map(mappings)
    regex_rules = build_regex_rules(mappings)

    category, canonical_name = categorize_with_regex("UPI/DR/12345/SWIGGY/BANK", keyword_map, regex_rules)

    assert category == "lunch"
    assert canonical_name == "Swiggy"


def test_extract_upi_counterparty_name() -> None:
    name = extract_upi_counterparty_name("UPI/DR/421383083018/JAYSHRI/FDRL/")
    assert name == "Jayshri"
