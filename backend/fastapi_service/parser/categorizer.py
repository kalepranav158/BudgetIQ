from typing import Iterable

DEFAULT_CATEGORIES = {
    "cash_withdrawal",
    "extra",
    "lunch",
    "other",
    "recharge",
    "tea",
    "credit",
}


def build_keyword_map(mappings: Iterable[dict]) -> dict[str, str]:
    keyword_map: dict[str, str] = {}
    for item in mappings:
        keyword = str(item.get("keyword", "")).strip().upper()
        category = str(item.get("category", "other")).strip().lower()
        if not keyword:
            continue
        keyword_map[keyword] = category if category in DEFAULT_CATEGORIES else "other"
    return keyword_map


def categorize_description(description: str, keyword_map: dict[str, str]) -> str:
    text = description.upper()
    for keyword, category in keyword_map.items():
        if keyword in text:
            return category
    return "other"
