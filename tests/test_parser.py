from decimal import Decimal

from backend.fastapi_service.parser.pdf_parser import _parse_decimal, _parse_sbi_date


def test_parse_sbi_date_format() -> None:
    assert _parse_sbi_date("01 Jul 2024") == "2024-07-01"


def test_parse_decimal_with_comma() -> None:
    assert _parse_decimal("12,345.67") == Decimal("12345.67")
