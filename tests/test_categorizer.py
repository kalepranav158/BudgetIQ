from backend.fastapi_service.parser.categorizer import build_keyword_map, categorize_description


def test_categorizer_uses_keyword_map() -> None:
    mappings = [
        {"keyword": "ZOMATO", "category": "lunch"},
        {"keyword": "ATM", "category": "cash_withdrawal"},
    ]

    keyword_map = build_keyword_map(mappings)

    assert categorize_description("UPI/ZOMATO ORDER", keyword_map) == "lunch"
    assert categorize_description("ATM CASH WD", keyword_map) == "cash_withdrawal"
    assert categorize_description("UNKNOWN MERCHANT", keyword_map) == "other"
