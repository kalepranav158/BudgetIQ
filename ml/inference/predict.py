from __future__ import annotations

import argparse

from backend.models.classifier import TransactionClassifier
from backend.services.categorization import HybridTransactionCategorizer


def main() -> None:
    parser = argparse.ArgumentParser(description='Predict a transaction category using the hybrid rule and ML pipeline.')
    parser.add_argument('text', help='Transaction text, for example: Paid to mess')
    parser.add_argument('--counterparty', default='', help='Optional extracted merchant or counterparty text')
    parser.add_argument('--direction', default='debit', choices=['debit', 'credit'], help='Transaction direction')
    args = parser.parse_args()

    categorizer = HybridTransactionCategorizer(classifier=TransactionClassifier())
    decision = categorizer.categorize(
        description=args.text,
        counterparty=args.counterparty,
        direction=args.direction,
    )
    print(f'category={decision.category} source={decision.source}')


if __name__ == '__main__':
    main()
