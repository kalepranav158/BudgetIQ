from typing import Iterable
import re

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
        if str(item.get("kind", "keyword")).lower() != "keyword":
            continue
        keyword = str(item.get("keyword", "")).strip().upper()
        category = str(item.get("category", "other")).strip().lower()
        if not keyword:
            continue
        keyword_map[keyword] = category if category in DEFAULT_CATEGORIES else "other"
    return keyword_map


def build_regex_rules(mappings: Iterable[dict]) -> list[tuple[re.Pattern[str], str, str, int]]:
    rules: list[tuple[re.Pattern[str], str, str, int]] = []
    for item in mappings:
        if str(item.get("kind", "")).lower() != "regex":
            continue

        pattern = str(item.get("pattern", "")).strip()
        if not pattern:
            continue

        name = str(item.get("name", "Unknown")).strip() or "Unknown"
        category = str(item.get("category", "other")).strip().lower()
        priority = int(item.get("priority", 100))

        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            continue

        safe_category = category if category in DEFAULT_CATEGORIES else "other"
        rules.append((compiled, name, safe_category, priority))

    rules.sort(key=lambda row: row[3])
    return rules


def extract_upi_counterparty_name(description: str) -> str | None:
    text = description.strip()

    # Handles common formats like UPI/DR/.../JAYSHRI/FDRL or UPI/CR/.../NARAYAN /SBI
    slash_chunks = [chunk.strip() for chunk in text.split("/")]
    if len(slash_chunks) >= 4 and slash_chunks[0].upper().startswith("UPI"):
        preferred_indexes = (3, 4)
        for index in preferred_indexes:
            if index >= len(slash_chunks):
                continue
            candidate = re.sub(r"[^A-Za-z\s]", "", slash_chunks[index]).strip()
            if candidate and candidate.lower() not in {"upi", "dr", "cr"}:
                return re.sub(r"\s+", " ", candidate).title()

    # Fallback for sentence style descriptions.
    match = re.search(r"(?:transfer\s+(?:to|from)|paid\s+to|received\s+from)\s+([A-Za-z][A-Za-z\s]{1,40})", text, re.IGNORECASE)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip().title()

    return None


def categorize_description(description: str, keyword_map: dict[str, str]) -> str:
    text = description.upper()
    for keyword, category in keyword_map.items():
        if keyword in text:
            return category
    return "other"


def categorize_with_regex(
    description: str,
    keyword_map: dict[str, str],
    regex_rules: list[tuple[re.Pattern[str], str, str, int]],
) -> tuple[str, str | None]:
    for compiled, canonical_name, category, _ in regex_rules:
        if compiled.search(description):
            return category, canonical_name

    return categorize_description(description, keyword_map), extract_upi_counterparty_name(description)


def infer_transaction_subtype(description: str, tx_type: str) -> str:
    text = description.lower()
    normalized_type = tx_type.lower()

    if "atm" in text or "cash withdrawal" in text or "withdrawal" in text:
        return "atm_withdrawal"

    if normalized_type == "debit" and "upi" in text and (
        "transfer to" in text or " to " in text or "sent" in text or "dr/" in text
    ):
        return "transfer_out"

    if normalized_type == "credit" and "upi" in text and (
        "transfer from" in text or " from " in text or "received" in text or "cr/" in text
    ):
        return "transfer_in"

    if normalized_type == "credit" and "salary" in text:
        return "salary"

    if normalized_type == "credit" and "refund" in text:
        return "refund"

    return "expense" if normalized_type == "debit" else "transfer_in"
