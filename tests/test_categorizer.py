from backend.fastapi_service.parser.categorizer import (
    build_account_rules,
    build_keyword_map,
    build_regex_rules,
    categorize_description,
    categorize_transaction,
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


def test_account_mapping_has_highest_priority() -> None:
    description = "TRANSFER TO 4897694162092 UPI/DR/510791183658/MAYURESH/YESB/q731754728/UPI"
    mappings = [
        {
            "kind": "account",
            "upi_id": "YESB/Q731754728",
            "name": "MAYURESH",
            "category": "lunch",
            "priority": 1,
        },
        {
            "kind": "regex",
            "name": "GenericTransfer",
            "pattern": r"TRANSFER TO",
            "category": "other",
            "priority": 10,
        },
        {"kind": "keyword", "keyword": "UPI", "category": "tea"},
    ]

    account_rules = build_account_rules(mappings)
    regex_rules = build_regex_rules(mappings)
    keyword_map = build_keyword_map(mappings)

    category, source, confidence, canonical_name = categorize_transaction(
        description=description,
        keyword_map=keyword_map,
        regex_rules=regex_rules,
        account_rules=account_rules,
    )

    assert category == "lunch"
    assert source == "account_rule"
    assert confidence == 1.0
    assert canonical_name == "Mayuresh"


def test_account_mapping_name_only_match_without_account_number() -> None:
    description = "UPI/DR/510700673411/HEMANT"
    mappings = [
        {
            "kind": "account",
            "upi_id": "",
            "name": "HEMANT",
            "category": "tea",
            "priority": 1,
        },
        {"kind": "keyword", "keyword": "UPI", "category": "other"},
    ]

    account_rules = build_account_rules(mappings)
    regex_rules = build_regex_rules(mappings)
    keyword_map = build_keyword_map(mappings)

    category, source, confidence, canonical_name = categorize_transaction(
        description=description,
        keyword_map=keyword_map,
        regex_rules=regex_rules,
        account_rules=account_rules,
    )

    assert category == "tea"
    assert source == "account_rule"
    assert confidence == 1.0
    assert canonical_name == "Hemant"
