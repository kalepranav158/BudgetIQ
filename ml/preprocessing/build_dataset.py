from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sqlalchemy import select

from backend.models.db import TransactionRecord
from backend.utils.preprocessing import normalize_text
from database.connection.session import SessionLocal, init_db


def build_dataset(output_path: Path) -> int:
    init_db()
    rows_written = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session, output_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['text', 'counterparty', 'category'])
        writer.writeheader()
        transactions = session.scalars(select(TransactionRecord).order_by(TransactionRecord.id)).all()
        for txn in transactions:
            if not txn.category:
                continue
            writer.writerow(
                {
                    'text': normalize_text(txn.description),
                    'counterparty': normalize_text(txn.counterparty),
                    'category': txn.category,
                }
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
    args = parser.parse_args()
    output_path = Path(args.output)
    rows_written = build_dataset(output_path)
    print(f'Wrote {rows_written} training rows to {output_path}')


if __name__ == '__main__':
    main()
