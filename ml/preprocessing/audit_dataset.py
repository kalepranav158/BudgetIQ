from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def audit_class_distribution(dataset_path: Path, output_path: Path, label_col: str = "category") -> dict:
    with dataset_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    labels = [str(row.get(label_col) or "").strip().lower() for row in rows if str(row.get(label_col) or "").strip()]
    counts = Counter(labels)
    total = max(1, len(labels))

    report: dict[str, dict] = {}
    for category, count in counts.most_common():
        report[category] = {
            "count": int(count),
            "pct": round((100.0 * count) / total, 2),
            "trainable": bool(count >= 5),
            "note": "OK" if count >= 20 else ("sparse" if count >= 5 else "SKIP - below threshold"),
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit class distribution for classification dataset.")
    parser.add_argument("--dataset", default="ml/data/training_dataset.csv", help="Input classification dataset CSV")
    parser.add_argument("--output", default="ml/data/class_audit.json", help="Output JSON report path")
    parser.add_argument("--label-col", default="category", help="Label column name")
    args = parser.parse_args()

    report = audit_class_distribution(Path(args.dataset), Path(args.output), label_col=args.label_col)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
