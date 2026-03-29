import os
from unittest.mock import patch

import django
from django.test import Client
from fastapi.testclient import TestClient

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.fastapi_service.main import app


def test_fastapi_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_django_health_endpoint() -> None:
    client = Client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("backend.django_app.views.parse_pdf_with_fastapi")
def test_upload_pdf_uses_parser_payload(mock_parse) -> None:
    mock_parse.return_value = {
        "transactions": [
            {
                "date": "2024-07-01",
                "description": "UPI/ZOMATO",
                "amount": "249.00",
                "type": "debit",
                "balance": "1000.00",
                "category": "lunch",
            }
        ],
        "summaries": [
            {
                "date": "2024-07-01",
                "cash_withdrawal": "0.00",
                "extra": "0.00",
                "lunch": "249.00",
                "other": "0.00",
                "recharge": "0.00",
                "tea": "0.00",
                "credit": "0.00",
                "total_debit": "249.00",
                "total_credit": "0.00",
            }
        ],
    }

    client = Client()
    with open("july2024.pdf", "rb") as handle:
        response = client.post("/upload-pdf", {"file": handle, "password": ""})

    assert response.status_code == 201
    body = response.json()
    assert body["saved_transactions"] == 1
    assert len(body["transactions"]) == 1
    assert len(body["summaries"]) == 1
