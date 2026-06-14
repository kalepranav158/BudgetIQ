"""Active learning loop: flag low-confidence predictions and trigger retraining."""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import argparse
import json
import logging
from datetime import datetime, timezone

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction, LowConfidenceFlagRecord, RetrainingCycle


logger = logging.getLogger(__name__)


def flag_low_confidence_transactions(confidence_threshold: float = 0.6) -> int:
    """Flag transactions with confidence below threshold for human review.
    
    Args:
        confidence_threshold: Minimum confidence to skip flagging (default 0.6).
    
    Returns:
        Count of newly flagged transactions.
    """
    # Find ML-predicted transactions below threshold that aren't already flagged
    low_confidence_txs = Transaction.objects.filter(
        category_source="ml",
        confidence__lt=confidence_threshold,
    ).exclude(
        low_confidence_flag__isnull=False
    )

    flagged_count = 0
    for tx in low_confidence_txs:
        flag, created = LowConfidenceFlagRecord.objects.get_or_create(
            transaction=tx,
            defaults={
                "original_category": tx.category,
                "original_confidence": tx.confidence,
                "confidence_threshold": confidence_threshold,
                "status": "flagged",
            },
        )
        if created:
            flagged_count += 1

    if flagged_count > 0:
        logger.info(f"Flagged {flagged_count} low-confidence transactions (threshold={confidence_threshold})")

    return flagged_count


def capture_corrections(corrections_csv_path: Path | None = None) -> int:
    """Capture human corrections from a CSV file or mark existing flags as reviewed.
    
    CSV format: transaction_id, corrected_category, notes
    
    Args:
        corrections_csv_path: Optional path to corrections CSV.
    
    Returns:
        Count of corrections applied.
    """
    corrections_applied = 0

    if corrections_csv_path and corrections_csv_path.exists():
        import csv
        with corrections_csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    tx_id = int(row["transaction_id"])
                    corrected_cat = row["corrected_category"].strip().lower()
                    notes = row.get("notes", "").strip()

                    flag = LowConfidenceFlagRecord.objects.get(transaction_id=tx_id)
                    flag.corrected_category = corrected_cat
                    flag.human_review_notes = notes
                    flag.status = "corrected"
                    flag.corrected_at = datetime.now(timezone.utc)
                    flag.save()
                    corrections_applied += 1
                except (ValueError, LowConfidenceFlagRecord.DoesNotExist):
                    continue

        logger.info(f"Captured {corrections_applied} corrections from CSV")

    return corrections_applied


def check_and_trigger_retraining(
    retraining_threshold: int = 80,
    confidence_threshold: float = 0.6,
) -> dict:
    """Check if retraining should be triggered and initiate if threshold met.
    
    Args:
        retraining_threshold: Min corrected records to trigger retraining (default 80).
        confidence_threshold: Confidence threshold for flagging.
    
    Returns:
        Status dict with trigger decision.
    """
    corrected_count = LowConfidenceFlagRecord.objects.filter(status="corrected").count()

    if corrected_count < retraining_threshold:
        return {
            "triggered": False,
            "reason": f"Only {corrected_count}/{retraining_threshold} corrections accumulated",
        }

    # Create retraining cycle
    cycle_id = f"cycle_{datetime.now(timezone.utc).timestamp()}"
    cycle = RetrainingCycle.objects.create(
        cycle_id=cycle_id,
        status="pending",
        trigger_reason=f"{corrected_count} corrections with confidence < {confidence_threshold}",
        corrections_count=corrected_count,
    )

    logger.info(f"Retraining triggered: {cycle_id} with {corrected_count} corrections")

    return {
        "triggered": True,
        "cycle_id": cycle_id,
        "corrections_count": corrected_count,
        "message": f"Retraining cycle {cycle_id} created",
    }


def get_active_learning_report() -> dict:
    """Generate report on active learning status."""
    total_flagged = LowConfidenceFlagRecord.objects.filter(status="flagged").count()
    total_reviewed = LowConfidenceFlagRecord.objects.filter(status="reviewed").count()
    total_corrected = LowConfidenceFlagRecord.objects.filter(status="corrected").count()
    pending_cycles = RetrainingCycle.objects.filter(status="pending").count()
    completed_cycles = RetrainingCycle.objects.filter(status="completed").count()

    return {
        "flagged_pending_review": total_flagged,
        "reviewed": total_reviewed,
        "corrected": total_corrected,
        "pending_retraining_cycles": pending_cycles,
        "completed_retraining_cycles": completed_cycles,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Active learning loop for classifier retraining.")
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.6,
        help="Confidence threshold below which to flag predictions (default 0.6)",
    )
    parser.add_argument(
        "--retraining-threshold",
        type=int,
        default=80,
        help="Min corrected records to trigger retraining (default 80)",
    )
    parser.add_argument(
        "--flag",
        action="store_true",
        help="Flag low-confidence transactions",
    )
    parser.add_argument(
        "--capture-corrections",
        type=str,
        default=None,
        help="Path to CSV with corrections (transaction_id, corrected_category, notes)",
    )
    parser.add_argument(
        "--check-retraining",
        action="store_true",
        help="Check and trigger retraining if threshold met",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print active learning status report",
    )

    args = parser.parse_args()

    if args.flag:
        count = flag_low_confidence_transactions(confidence_threshold=args.confidence_threshold)
        print(f"✓ Flagged {count} transactions")

    if args.capture_corrections:
        count = capture_corrections(corrections_csv_path=Path(args.capture_corrections))
        print(f"✓ Captured {count} corrections")

    if args.check_retraining:
        result = check_and_trigger_retraining(
            retraining_threshold=args.retraining_threshold,
            confidence_threshold=args.confidence_threshold,
        )
        print(json.dumps(result, indent=2))

    if args.report:
        report = get_active_learning_report()
        print(json.dumps(report, indent=2))

    if not any([args.flag, args.capture_corrections, args.check_retraining, args.report]):
        # Default: run full loop
        flagged = flag_low_confidence_transactions(confidence_threshold=args.confidence_threshold)
        corrected = capture_corrections()
        retrain = check_and_trigger_retraining(
            retraining_threshold=args.retraining_threshold,
            confidence_threshold=args.confidence_threshold,
        )
        report = get_active_learning_report()

        print(json.dumps({
            "flagged": flagged,
            "corrected": corrected,
            "retraining": retrain,
            "status": report,
        }, indent=2))


if __name__ == "__main__":
    main()
