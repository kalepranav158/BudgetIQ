from collections import defaultdict
from decimal import Decimal

DEBIT_CATEGORIES = ["cash_withdrawal", "extra", "lunch", "other", "recharge", "tea"]
ALL_COLUMNS = DEBIT_CATEGORIES + ["credit", "total_debit", "total_credit"]


def build_daily_summaries(transactions: list[dict]) -> list[dict]:
    grouped: dict[str, dict[str, Decimal]] = defaultdict(lambda: {column: Decimal("0.00") for column in ALL_COLUMNS})

    for tx in transactions:
        date = str(tx["date"])
        tx_type = str(tx["type"]).lower()
        amount = Decimal(str(tx["amount"]))
        category = str(tx.get("category", "other")).lower()

        if tx_type == "credit":
            grouped[date]["credit"] += amount
            grouped[date]["total_credit"] += amount
        else:
            debit_category = category if category in DEBIT_CATEGORIES else "other"
            grouped[date][debit_category] += amount
            grouped[date]["total_debit"] += amount

    summaries: list[dict] = []
    for date, values in sorted(grouped.items(), key=lambda item: item[0]):
        row = {"date": date}
        row.update(values)
        summaries.append(row)

    return summaries
