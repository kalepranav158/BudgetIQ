from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.services.transaction_service import TransactionIngestionService
from database.connection.session import SessionLocal, init_db


def main() -> None:
    parser = argparse.ArgumentParser(description='Import an SBI/YONO PDF statement into the normalized budget database.')
    parser.add_argument('pdf_path', help='Path to the password-protected bank statement PDF')
    parser.add_argument('--password', default=None, help='Optional PDF password override')
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        raise SystemExit(f'PDF file not found: {pdf_path}')

    init_db()
    with pdf_path.open('rb') as handle, SessionLocal() as session:
        service = TransactionIngestionService(session)
        summary = service.import_statement(
            pdf_source=handle,
            source_name=pdf_path.name,
            password=args.password,
        )
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()