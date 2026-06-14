from __future__ import annotations

import argparse
import csv
from pathlib import Path

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from backend.django_app.models import Transaction

from ml.features import build_feature_row
from ml.utils import normalize_text


def _load_rows_from_csv(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def build_dataset(output_path: Path, clean_input_path: Path | None = None) -> int:
    rows_written = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    source_rows = _load_rows_from_csv(clean_input_path) if clean_input_path else []
    if not source_rows:
        source_rows = list(
            Transaction.objects.all().order_by('id').values(
                'date',
                'description',
                'amount',
                'type',
                'subtype',
                'category',
                'category_source',
                'confidence',
            )
        )

    with output_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'date',
                'description',
                'text',
                'counterparty',
                'amount',
                'amount_log1p',
                'amount_bucket',
                'weekday',
                'month',
                'year',
                'day_of_month',
                'is_weekend',
                'prefix_bigram',
                'type',
                'subtype',
                'category',
                'category_source',
                'confidence',
                'is_upi',
                'is_transfer',
                'combined_text',
            ],
        )
        writer.writeheader()
        for txn in source_rows:
            category = normalize_text(txn.get('category'))
            if not category:
                continue
            feature_row = build_feature_row(txn)
            feature_row['category_source'] = str(txn.get('category_source') or 'keyword').strip()
            feature_row['confidence'] = float(txn.get('confidence') or 0.0)
            writer.writerow(
                {key: feature_row.get(key, '') for key in writer.fieldnames}
            )
            rows_written += 1
    return rows_written


def main() -> None:
    parser = argparse.ArgumentParser(description='Export labeled transactions into a CSV training dataset.')
    parser.add_argument(
        '--output',
        default='ml/data/training_dataset.csv',
        help='CSV file path for the exported training data',
    )
    parser.add_argument(
        '--clean-input',
        default='ml/data/clean_transactions.csv',
        help='Optional sanitized transaction CSV input. Falls back to DB when absent.',
    )
    args = parser.parse_args()
    output_path = Path(args.output)
    clean_input_path = Path(args.clean_input)
    rows_written = build_dataset(output_path, clean_input_path=clean_input_path)
    print(f'Wrote {rows_written} training rows to {output_path}')


if __name__ == '__main__':
    main()
