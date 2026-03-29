import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class FastApiParseError(RuntimeError):
    pass


def parse_pdf_with_fastapi(file_name: str, file_bytes: bytes, password: str | None, mappings: list[dict]) -> dict:
    files = {"file": (file_name, file_bytes, "application/pdf")}
    data = {
        "password": password or "",
        "mappings": json.dumps(mappings),
    }

    try:
        response = requests.post(settings.FASTAPI_PARSE_URL, files=files, data=data, timeout=120)
    except requests.RequestException as exc:
        logger.exception("Failed to call FastAPI parser")
        raise FastApiParseError("Failed to reach FastAPI parser service") from exc

    if response.status_code != 200:
        raise FastApiParseError(f"FastAPI parser error: {response.status_code} {response.text}")

    payload = response.json()
    if "transactions" not in payload or "summaries" not in payload:
        raise FastApiParseError("FastAPI parser returned invalid payload")

    return payload
