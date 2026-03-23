from backend.utils.parsing import StatementParser


def test_text_line_parser_extracts_debit_transaction() -> None:
    parser = StatementParser()
    row = parser._parse_text_entry(
        '20 May 2025 TRANSFER TO 4897692162094 - UPI/DR/514028940936/NIRANJAN/YESB/q277333998/UPI 30.00 112.24'
    )
    assert row is not None
    assert row['date'] == '20 May 2025'
    assert 'TRANSFER TO' in row['details']
    assert row['debit'] == '30.00'
    assert row['balance'] == '112.24'
