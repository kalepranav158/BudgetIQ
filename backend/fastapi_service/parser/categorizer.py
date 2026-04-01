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


# Precompiled regex to extract UPI reference IDs of the form
#   YESB/Q208692237
# It is case-insensitive and tolerant of an optional trailing slash.
_UPI_ID_REGEX = re.compile(r"([A-Za-z][A-Za-z0-9]{1,9})/([A-Za-z0-9]{4,})/?", re.IGNORECASE)


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


def build_account_rules(mappings: Iterable[dict]) -> list[dict[str, str | int]]:
    """Build rules for UPI-based account mappings.

    Each rule expects:
      - kind: "account"
      - upi_id: normalized UPI reference (e.g. "YESB/Q208692237")
      - name: receiver name in UPPERCASE (e.g. "HEMANT")
    """

    rules: list[dict[str, str | int]] = []
    for item in mappings:
        if str(item.get("kind", "")).lower() != "account":
            continue

        upi_id = str(item.get("upi_id", "")).strip().upper()
        name = str(item.get("name", "")).strip().upper()
        if not upi_id and not name:
            # Ignore completely empty account rules
            continue

        category = str(item.get("category", "other")).strip().lower()
        priority = int(item.get("priority", 1))

        safe_category = category if category in DEFAULT_CATEGORIES else "other"
        rules.append(
            {
                "upi_id": upi_id,
                "name": name,
                "category": safe_category,
                "priority": priority,
            }
        )

    rules.sort(key=lambda row: int(row["priority"]))
    return rules


def extract_upi_details(text: str) -> dict[str, str | None]:
    """Extract UPI receiver name and UPI ID from a transaction description.

    Example input:
        "TRANSFER TO 4897694162092 UPI/DR/598732810891/HEMANT P/YESB/Q208692237/Payme"

    Returns (normalized):
        {"name": "HEMANT P", "upi_id": "YESB/Q208692237"}

    Normalization rules:
        - name   -> uppercased and stripped (spaces collapsed)
        - upi_id -> uppercased, trailing slash removed
    """

    text = (text or "").strip()
    receiver_name: str | None = None
    upi_id: str | None = None

    # Split description by '/' once for structural parsing (UPI/DR/..../NAME/BANK/REF/...)
    slash_chunks = [chunk.strip() for chunk in text.split("/") if chunk.strip()]

    # --- Receiver name extraction ---
    # Handles typical UPI formats like UPI/DR/.../JAYSHRI/FDRL or embedded after TRANSFER TO ...
    dr_cr_index: int | None = None
    if len(slash_chunks) >= 4:
        for i, chunk in enumerate(slash_chunks):
            upper = chunk.upper()
            if upper in {"DR", "CR"}:
                dr_cr_index = i
                break

        if dr_cr_index is not None:
            # After DR/CR comes transaction ID (digits), then the receiver name.
            candidate_indexes = (dr_cr_index + 2, dr_cr_index + 3)
            for idx in candidate_indexes:
                if idx >= len(slash_chunks):
                    continue
                raw = slash_chunks[idx]
                cleaned = re.sub(r"[^A-Za-z\s]", "", raw).strip()
                if cleaned and cleaned.lower() not in {"upi", "dr", "cr"}:
                    receiver_name = re.sub(r"\s+", " ", cleaned).upper()
                    break

        # Fallback: pure UPI prefix: UPI/DR/.../NAME/BANK/REF
        if receiver_name is None and slash_chunks[0].upper().startswith("UPI"):
            candidate_indexes = (3, 4)
            for idx in candidate_indexes:
                if idx >= len(slash_chunks):
                    continue
                raw = slash_chunks[idx]
                cleaned = re.sub(r"[^A-Za-z\s]", "", raw).strip()
                if cleaned and cleaned.lower() not in {"upi", "dr", "cr"}:
                    receiver_name = re.sub(r"\s+", " ", cleaned).upper()
                    break

    # Final fallback: sentence style descriptions ("paid to John Doe" etc.).
    if receiver_name is None:
        match = re.search(
            r"(?:transfer\s+(?:to|from)|paid\s+to|received\s+from)\s+([A-Za-z][A-Za-z\s]{1,40})",
            text,
            re.IGNORECASE,
        )
        if match:
            cleaned = re.sub(r"\s+", " ", match.group(1)).strip()
            if cleaned:
                receiver_name = cleaned.upper()

    # --- UPI ID extraction ---
    # Prefer structured extraction using the DR/CR marker when available:
    #   UPI/DR/<TXID>/<NAME>/<BANK>/<REF>/...
    if dr_cr_index is not None and len(slash_chunks) > dr_cr_index + 4:
        raw_bank = slash_chunks[dr_cr_index + 3]
        raw_ref = slash_chunks[dr_cr_index + 4]
        bank_clean = re.sub(r"[^A-Za-z0-9]", "", raw_bank).upper()
        ref_clean = re.sub(r"[^A-Za-z0-9]", "", raw_ref).upper()
        if bank_clean and ref_clean and bank_clean not in {"UPI", "DR", "CR"}:
            upi_id = f"{bank_clean}/{ref_clean}"

    # Fallback: flexible detection of patterns like YESB/Q208692237, with optional
    # slashes and case-insensitive, when structured parsing did not succeed.
    if upi_id is None:
        match_id = _UPI_ID_REGEX.search(text)
        if match_id:
            bank = match_id.group(1).upper().rstrip("/")
            ref = match_id.group(2).upper().rstrip("/")
            if bank not in {"UPI", "DR", "CR"}:
                upi_id = f"{bank}/{ref}"

    return {"name": receiver_name, "upi_id": upi_id}


def extract_upi_counterparty_name(description: str) -> str | None:
    """Backward-compatible wrapper that returns only the counterparty name.

    This maintains the previous public API while delegating to extract_upi_details.
    """

    details = extract_upi_details(description)
    name = details.get("name")
    if not name:
        return None
    # Historically this function returned Title Case names.
    return name.title()


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


def categorize_transaction(
    description: str,
    keyword_map: dict[str, str],
    regex_rules: list[tuple[re.Pattern[str], str, str, int]],
    account_rules: list[dict[str, str | int]],
    ml_predicted_category: str | None = None,
) -> tuple[str, str, float, str | None]:
    details = extract_upi_details(description)
    extracted_name = details.get("name") or None
    extracted_upi_id = details.get("upi_id") or None
    extracted_name_upper = extracted_name.upper() if extracted_name else ""
    extracted_upi_upper = extracted_upi_id.upper() if extracted_upi_id else ""

    # UPI-based mappings have highest priority and are evaluated before
    # regex and keyword mappings.
    for rule in account_rules:
        rule_upi = str(rule.get("upi_id", "")).strip().upper()
        mapped_name = str(rule.get("name", "")).strip().upper()

        both_present = bool(rule_upi and mapped_name and extracted_upi_upper and extracted_name_upper)
        full_match = both_present and rule_upi == extracted_upi_upper and mapped_name == extracted_name_upper

        # Highest confidence when both UPI ID and name match exactly.
        if full_match:
            canonical_name = extracted_name.title() if extracted_name else mapped_name.title()
            return str(rule["category"]), "account_rule", 1.0, canonical_name

        # Fallback: allow name-only mappings (no UPI ID stored) for backward
        # compatibility and simpler rules, as long as the receiver name matches.
        if not rule_upi and mapped_name and extracted_name_upper and mapped_name == extracted_name_upper:
            canonical_name = extracted_name.title() if extracted_name else mapped_name.title()
            return str(rule["category"]), "account_rule", 1.0, canonical_name

    for compiled, canonical_name, category, _ in regex_rules:
        if compiled.search(description):
            return category, "regex", 1.0, canonical_name

    keyword_category = categorize_description(description, keyword_map)
    if keyword_category != "other":
        return keyword_category, "keyword", 1.0, extracted_name

    if ml_predicted_category:
        return ml_predicted_category, "ml", 0.6, extracted_name

    return "other", "keyword", 0.0, extracted_name


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
