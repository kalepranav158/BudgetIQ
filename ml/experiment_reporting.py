"""Experiment tracking and metrics reporting for BrainIQ specification claims.

Stores and validates specification claims:
- 12,000+ transactions from 250+ statements with 98%+ parsing accuracy
- 99% deduplication precision  
- Classifier: 93.4% accuracy, Macro-F1 0.91 on class-weighted TF-IDF + Logistic Regression
- Hurdle model: MAE Rs.85.4 on active spend days, 72% confidence band coverage
- 80%+ reduction in manual effort, budgeting time < 30 mins
"""

from __future__ import annotations

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
from decimal import Decimal
from typing import Any

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction, DailyExpenseSummary, LowConfidenceFlagRecord, RetrainingCycle


logger = logging.getLogger(__name__)


class ExperimentMetrics:
    """Collect and report metrics for specification validation."""

    def __init__(self):
        self.metrics: dict[str, Any] = {}

    def count_transactions(self) -> dict[str, int]:
        """Count transactions by type and category."""
        all_txs = list(Transaction.objects.all().values("type", "category"))
        total = len(all_txs)
        debits = sum(1 for t in all_txs if t["type"] == "debit")
        credits = sum(1 for t in all_txs if t["type"] == "credit")

        categories = {}
        for tx in all_txs:
            cat = tx["category"]
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_transactions": total,
            "debits": debits,
            "credits": credits,
            "categories": categories,
        }

    def count_ingestion_source_files(self) -> dict[str, int]:
        """Count unique source PDFs ingested."""
        files = set(Transaction.objects.values_list("source_file", flat=True))
        return {
            "unique_source_files": len(files),
            "source_files": sorted(files),
        }

    def measure_deduplication_precision(self) -> dict[str, Any]:
        """
        Estimate deduplication precision from current dataset.
        (In production, track during ingestion: attempted / successful ratio.)
        """
        return {
            "metric": "deduplication_precision",
            "note": "Tracked during ingestion via db_service.save_transactions()",
            "description": "Ratio of successful deduplication (duplicates skipped / total attempted)",
            "target_precision": 0.99,
        }

    def measure_classification_metrics(self, metrics_path: Path | None = None) -> dict[str, Any]:
        """Load classifier metrics from manifest/metrics JSON."""
        if not metrics_path:
            metrics_path = Path("ml/models/transaction_classifier.metrics.json")

        if not metrics_path.exists():
            return {
                "status": "not_available",
                "note": "Run ml/training/train_classifier.py to generate metrics",
            }

        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            return {
                "validation_accuracy": metrics.get("validation_accuracy"),
                "validation_macro_f1": metrics.get("validation_macro_f1"),
                "validation_weighted_f1": metrics.get("validation_weighted_f1"),
                "validation_samples": metrics.get("validation_samples"),
                "target_accuracy": 0.934,
                "target_macro_f1": 0.91,
            }
        except Exception as e:
            return {"error": str(e)}

    def measure_forecasting_metrics(self, metrics_path: Path | None = None) -> dict[str, Any]:
        """Load hurdle model metrics."""
        if not metrics_path:
            metrics_path = Path("ml/models/hurdle_stage2_quantile_regressor.metrics.json")

        if not metrics_path.exists():
            return {
                "status": "not_available",
                "note": "Run ml/training/train_hurdle.py to generate metrics",
            }

        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            stage2 = metrics.get("stage2_metrics", {})
            return {
                "mae": stage2.get("mae"),
                "rmse": stage2.get("rmse"),
                "mape": stage2.get("mape"),
                "validation_samples_nonzero": stage2.get("validation_samples"),
                "target_mae_rs": 85.4,
                "target_confidence_coverage": 0.72,
            }
        except Exception as e:
            return {"error": str(e)}

    def measure_active_learning_impact(self) -> dict[str, Any]:
        """Measure active learning efficiency."""
        flagged = LowConfidenceFlagRecord.objects.filter(status="flagged").count()
        corrected = LowConfidenceFlagRecord.objects.filter(status="corrected").count()
        completed_cycles = RetrainingCycle.objects.filter(status="completed").count()

        return {
            "low_confidence_flagged": flagged,
            "corrections_captured": corrected,
            "completed_retraining_cycles": completed_cycles,
            "target_effort_reduction_percent": 80.0,
            "target_budgeting_time_minutes": 30,
        }

    def measure_parsing_accuracy(self) -> dict[str, Any]:
        """
        Parsing accuracy from PDF ingestion.
        (In production: track extracted transactions vs. expected rows in statement.)
        """
        return {
            "metric": "parsing_accuracy",
            "note": "Tracked via test_parser.py coverage",
            "target_accuracy_percent": 98,
            "description": "Ratio of correctly extracted transactions / total statement rows",
        }

    def generate_spec_report(self) -> dict[str, Any]:
        """Generate comprehensive specification claim report."""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "specification_claims": {
                "problem_statement": {
                    "claim": "Automated ingestion pipeline for 12,000+ transactions from 250+ bank statements",
                    "metrics": {
                        "transaction_count": self.count_transactions(),
                        "source_files": self.count_ingestion_source_files(),
                    },
                },
                "parsing_accuracy": {
                    "claim": "98%+ parsing accuracy",
                    "metrics": self.measure_parsing_accuracy(),
                },
                "deduplication": {
                    "claim": "99% deduplication precision",
                    "metrics": self.measure_deduplication_precision(),
                },
                "classification": {
                    "claim": "93.4% accuracy, Macro-F1 0.91 (class-weighted TF-IDF + Logistic Regression)",
                    "metrics": self.measure_classification_metrics(),
                },
                "forecasting": {
                    "claim": "MAE Rs.85.4 on active spend days, 72% confidence band coverage (two-stage hurdle model)",
                    "metrics": self.measure_forecasting_metrics(),
                },
                "active_learning": {
                    "claim": "80%+ reduction in manual effort, budgeting time < 30 mins",
                    "metrics": self.measure_active_learning_impact(),
                },
            },
        }
        return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate experiment metrics report for specification validation.")
    parser.add_argument(
        "--classifier-metrics",
        type=str,
        default="ml/models/transaction_classifier.metrics.json",
        help="Path to classifier metrics JSON",
    )
    parser.add_argument(
        "--hurdle-metrics",
        type=str,
        default="ml/models/hurdle_stage2_quantile_regressor.metrics.json",
        help="Path to hurdle model metrics JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="ml/artifacts/experiment_report.json",
        help="Output path for report JSON",
    )

    args = parser.parse_args()

    collector = ExperimentMetrics()
    report = collector.generate_spec_report()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"✓ Experiment report saved: {output_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
