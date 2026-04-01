import json
import os
from pathlib import Path
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


def test_fastapi_parse_all_pdfs_in_io() -> None:
    client = TestClient(app)
    io_dir = Path(__file__).resolve().parents[1] / "IO"
    pdf_files = sorted(io_dir.glob("*.pdf"))

    assert pdf_files, "No PDF files found in IO directory"

    for pdf_file in pdf_files:
        with pdf_file.open("rb") as handle:
            response = client.post(
                "/parse-pdf",
                files={"file": (pdf_file.name, handle, "application/pdf")},
                data={
                    "password": "1508@6239",
                    "mappings": "[]",
                    "persist": "false",
                },
            )

        assert response.status_code == 200, f"Failed parsing {pdf_file.name}: {response.text}"
        payload = response.json()
        assert "transactions" in payload
        assert "summaries" in payload


def test_django_health_endpoint() -> None:
    client = Client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_fastapi_get_regex_mappings_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/get_regex_mappings")

    assert response.status_code == 200
    payload = response.json()
    assert "regex_mappings" in payload
    assert isinstance(payload["regex_mappings"], list)


def test_fastapi_get_category_mappings_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/get_category_mappings")

    assert response.status_code == 200
    payload = response.json()
    assert "category_mappings" in payload
    assert isinstance(payload["category_mappings"], list)


@patch("backend.fastapi_service.main.extract_transactions_from_pdf")
def test_fastapi_account_mapping_override(mock_extract) -> None:
    mock_extract.return_value = [
        {
            "date": "2026-03-30",
            "description": "TRANSFER TO 4897694162092 UPI/DR/510791183658/MAYURESH/YESB/q731754728/UPI",
            "amount": "120.00",
            "type": "debit",
            "balance": "1000.00",
        }
    ]

    client = TestClient(app)
    mappings = [
        {
            "kind": "account",
            "upi_id": "YESB/Q731754728",
            "name": "MAYURESH",
            "category": "lunch",
            "priority": 1,
        }
    ]

    response = client.post(
        "/parse-pdf",
        files={"file": ("sample.pdf", b"fake-pdf-bytes", "application/pdf")},
        data={
            "password": "1508@6239",
            "mappings": json.dumps(mappings),
            "persist": "false",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "transactions" in payload
    assert isinstance(payload["transactions"], list)

    account_rule_rows = [
        tx for tx in payload["transactions"] if tx.get("category_source") == "account_rule"
    ]
    assert account_rule_rows
    first = account_rule_rows[0]
    assert first["category"] == "lunch"
    assert first["confidence"] == 1.0


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
