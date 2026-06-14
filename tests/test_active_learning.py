"""Tests for active learning loop and retraining triggers."""

import os
from datetime import datetime, timezone
from decimal import Decimal

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction, LowConfidenceFlagRecord, RetrainingCycle
from ml.active_learning import (
    flag_low_confidence_transactions,
    capture_corrections,
    check_and_trigger_retraining,
    get_active_learning_report,
)


@pytest.fixture
def clear_database():
    """Clear all active learning tables before each test."""
    LowConfidenceFlagRecord.objects.all().delete()
    RetrainingCycle.objects.all().delete()
    Transaction.objects.all().delete()
    yield


@pytest.fixture
def sample_low_confidence_transactions(clear_database):
    """Create transactions with low ML confidence."""
    transactions = []
    for i in range(5):
        tx = Transaction.objects.create(
            date="2026-01-01",
            description=f"Test transaction {i}",
            amount=Decimal("50.00"),
            type="debit",
            category="other",
            category_source="ml",
            confidence=0.55,  # Below default 0.6 threshold
            source_file="test.pdf",
        )
        transactions.append(tx)

    for i in range(3):
        tx = Transaction.objects.create(
            date="2026-01-02",
            description=f"High confidence tx {i}",
            amount=Decimal("30.00"),
            type="debit",
            category="lunch",
            category_source="ml",
            confidence=0.85,  # Above threshold
            source_file="test.pdf",
        )
        transactions.append(tx)

    return transactions


def test_flag_low_confidence_transactions(sample_low_confidence_transactions):
    """Test flagging of low-confidence predictions."""
    flagged_count = flag_low_confidence_transactions(confidence_threshold=0.6)

    assert flagged_count == 5

    # Check that flags were created
    flags = LowConfidenceFlagRecord.objects.filter(status="flagged")
    assert flags.count() == 5

    for flag in flags:
        assert flag.original_confidence < 0.6
        assert flag.status == "flagged"


def test_flag_does_not_duplicate(sample_low_confidence_transactions):
    """Test that flagging is idempotent (doesn't create duplicates)."""
    first_run = flag_low_confidence_transactions(confidence_threshold=0.6)
    second_run = flag_low_confidence_transactions(confidence_threshold=0.6)

    assert first_run == 5
    assert second_run == 0  # No new flags

    assert LowConfidenceFlagRecord.objects.filter(status="flagged").count() == 5


def test_high_confidence_not_flagged(sample_low_confidence_transactions):
    """Test that high-confidence predictions are not flagged."""
    flagged_count = flag_low_confidence_transactions(confidence_threshold=0.6)

    # Only low-confidence should be flagged
    assert flagged_count == 5

    # High-confidence transactions should have no flag
    high_conf_txs = Transaction.objects.filter(confidence__gte=0.6)
    for tx in high_conf_txs:
        assert not hasattr(tx, "low_confidence_flag") or tx.low_confidence_flag is None


def test_check_and_trigger_retraining_below_threshold(sample_low_confidence_transactions):
    """Test that retraining is not triggered when corrections are below threshold."""
    flag_low_confidence_transactions(confidence_threshold=0.6)

    # Mark only 3 as corrected (below 80 threshold)
    flags = LowConfidenceFlagRecord.objects.filter(status="flagged")[:3]
    for flag in flags:
        flag.corrected_category = "lunch"
        flag.status = "corrected"
        flag.save()

    result = check_and_trigger_retraining(retraining_threshold=80)

    assert result["triggered"] is False
    assert "Only 3/80" in result["reason"]


def test_check_and_trigger_retraining_above_threshold(sample_low_confidence_transactions):
    """Test that retraining is triggered when corrections exceed threshold."""
    flag_low_confidence_transactions(confidence_threshold=0.6)

    # Create 85 corrected records to exceed 80 threshold
    for i in range(85):
        tx = Transaction.objects.create(
            date="2026-02-01",
            description=f"Correction {i}",
            amount=Decimal("25.00"),
            type="debit",
            category="other",
            category_source="ml",
            confidence=0.50,
            source_file="test.pdf",
        )
        LowConfidenceFlagRecord.objects.create(
            transaction=tx,
            original_category="other",
            original_confidence=0.50,
            status="corrected",
            corrected_category="lunch",
        )

    result = check_and_trigger_retraining(retraining_threshold=80)

    assert result["triggered"] is True
    assert "cycle_id" in result
    assert result["corrections_count"] == 85

    # Check that cycle was created
    cycles = RetrainingCycle.objects.filter(cycle_id=result["cycle_id"])
    assert cycles.count() == 1
    assert cycles[0].status == "pending"


def test_get_active_learning_report(sample_low_confidence_transactions):
    """Test that active learning report is generated correctly."""
    flag_low_confidence_transactions(confidence_threshold=0.6)

    report = get_active_learning_report()

    assert "flagged_pending_review" in report
    assert "reviewed" in report
    assert "corrected" in report
    assert "pending_retraining_cycles" in report
    assert "timestamp" in report
    assert report["flagged_pending_review"] == 5
    assert report["reviewed"] == 0
    assert report["corrected"] == 0


def test_report_with_mixed_states(sample_low_confidence_transactions):
    """Test report with various flag states."""
    flag_low_confidence_transactions(confidence_threshold=0.6)

    flags = list(LowConfidenceFlagRecord.objects.all())
    flags[0].status = "corrected"
    flags[0].save()
    flags[1].status = "reviewed"
    flags[1].save()

    report = get_active_learning_report()

    assert report["flagged_pending_review"] == 3
    assert report["reviewed"] == 1
    assert report["corrected"] == 1


def test_retraining_cycle_creation(sample_low_confidence_transactions):
    """Test RetrainingCycle object creation and tracking."""
    flag_low_confidence_transactions(confidence_threshold=0.6)

    result = check_and_trigger_retraining(retraining_threshold=5, confidence_threshold=0.6)

    # Mark some as corrected to trigger
    flags = LowConfidenceFlagRecord.objects.filter(status="flagged")[:5]
    for flag in flags:
        flag.status = "corrected"
        flag.save()

    result = check_and_trigger_retraining(retraining_threshold=5)
    assert result["triggered"] is True

    cycle = RetrainingCycle.objects.get(cycle_id=result["cycle_id"])
    assert cycle.corrections_count == 5
    assert cycle.status == "pending"
    assert "corrections" in cycle.trigger_reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
