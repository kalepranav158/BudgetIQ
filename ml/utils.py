from __future__ import annotations

import re


def normalize_text(value: str | None) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip().lower())
    return text
