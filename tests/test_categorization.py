from backend.fastapi_service.parser.categorizer import build_keyword_map, categorize_description


def test_build_keyword_map_normalizes_keys_and_categories() -> None:
    mappings = [
        {"keyword": "  zOmAtO ", "category": "LUNCH"},
        {"keyword": "", "category": "tea"},
    ]

    result = build_keyword_map(mappings)

    assert result == {"ZOMATO": "lunch"}


def test_categorization_falls_back_to_other_when_not_mapped() -> None:
    keyword_map = {"SWIGGY": "lunch"}
    assert categorize_description("IMPS PAYMENT", keyword_map) == "other"


def test_short_keyword_does_not_match_inside_larger_word() -> None:
    keyword_map = {"TEA": "tea"}
    assert categorize_description("STEAK HOUSE", keyword_map) == "other"
    assert categorize_description("TEA STALL", keyword_map) == "tea"
