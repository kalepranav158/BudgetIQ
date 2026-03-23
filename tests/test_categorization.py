from backend.services.categorization import HybridTransactionCategorizer


def test_rule_based_food_category_from_keyword() -> None:
    categorizer = HybridTransactionCategorizer()
    decision = categorizer.categorize('Paid to hostel mess for dinner', counterparty='hostel mess', direction='debit')
    assert decision.category == 'mess'
    assert decision.source == 'rule'


def test_credit_defaults_to_income() -> None:
    categorizer = HybridTransactionCategorizer()
    decision = categorizer.categorize('TRANSFER FROM salary account', counterparty='company payroll', direction='credit')
    assert decision.category == 'income'
