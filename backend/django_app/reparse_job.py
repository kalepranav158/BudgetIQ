import re
from django.db import transaction
from backend.fastapi_service.parser.categorizer import build_account_rules, build_keyword_map, build_regex_rules, categorize_transaction
from backend.django_app.models import AccountCategoryMapping, CategoryMapping, RegexCategoryMapping
from backend.django_app.models import Transaction

def process_reparse_job(job):
    """Process a ReparseJob instance in-place. Updates job.result with counts.

    job.params expected keys vary by job.kind:
      - kind=keyword -> params: {"keyword": "...", "category": "..."}
      - kind=regex -> params: {"pattern": "...", "category": "..."}
      - kind=account -> params: {"upi_id": "...", "category": "..."}
    """
    kind = job.kind
    params = job.params or {}

    if kind == "all":
        keyword_map = build_keyword_map(
            [
                {"kind": "keyword", "keyword": row.keyword, "category": row.category}
                for row in CategoryMapping.objects.all()
            ]
        )
        regex_rules = build_regex_rules(
            [
                {"kind": "regex", "name": row.name, "pattern": row.pattern, "category": row.category, "priority": row.priority}
                for row in RegexCategoryMapping.objects.all()
            ]
        )
        account_rules = build_account_rules(
            [
                {"kind": "account", "upi_id": row.upi_id, "name": row.name, "category": row.category, "priority": row.priority}
                for row in AccountCategoryMapping.objects.all()
            ]
        )

        updated = 0
        qs = Transaction.objects.all().only("id", "description")
        for tx in qs.iterator(chunk_size=500):
            category, source, confidence, _ = categorize_transaction(tx.description or "", keyword_map, regex_rules, account_rules)
            Transaction.objects.filter(id=tx.id).update(category=category, category_source=source, confidence=confidence)
            updated += 1

        job.result = {"updated": updated}
        job.progress = 100
        job.status = "done"
        job.save()
        return

    if kind == "keyword":
        kw = str(params.get("keyword", "")).strip()
        cat = str(params.get("category", "other")).strip().lower() or "other"
        qs = Transaction.objects.filter(description__icontains=kw)
        updated = qs.update(category=cat, category_source="keyword", confidence=1.0)
        job.result = {"updated": updated}
        job.progress = 100
        job.status = "done"
        job.save()
        return

    if kind == "regex":
        pattern = str(params.get("pattern", "")).strip()
        cat = str(params.get("category", "other")).strip().lower() or "other"
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            job.status = "failed"
            job.error = f"invalid regex: {e}"
            job.save()
            return

        batch = 1000
        matched_ids = []
        total = 0
        qs = Transaction.objects.all().values_list("id", "description")
        for tid, desc in qs.iterator():
            total += 1
            if compiled.search(str(desc or "")):
                matched_ids.append(tid)
            if len(matched_ids) >= batch:
                with transaction.atomic():
                    Transaction.objects.filter(id__in=matched_ids).update(category=cat, category_source="regex", confidence=1.0)
                matched_ids = []
                # best-effort progress
                job.progress = min(95, int(total / 10000 * 100))
                job.save()

        if matched_ids:
            with transaction.atomic():
                Transaction.objects.filter(id__in=matched_ids).update(category=cat, category_source="regex", confidence=1.0)

        job.result = {"updated": "ok"}
        job.progress = 100
        job.status = "done"
        job.save()
        return

    if kind == "account":
        upi = str(params.get("upi_id", "")).strip()
        cat = str(params.get("category", "other")).strip().lower() or "other"
        # simple UPI matching: look for upi string in description
        batch = 1000
        matched = []
        total = 0
        qs = Transaction.objects.all().values_list("id", "description")
        for tid, desc in qs.iterator():
            total += 1
            if upi.upper() in str(desc or "").upper():
                matched.append(tid)
            if len(matched) >= batch:
                with transaction.atomic():
                    Transaction.objects.filter(id__in=matched).update(category=cat, category_source="account_rule", confidence=1.0)
                matched = []
                job.progress = min(95, int(total / 10000 * 100))
                job.save()

        if matched:
            with transaction.atomic():
                Transaction.objects.filter(id__in=matched).update(category=cat, category_source="account_rule", confidence=1.0)

        job.result = {"updated": "ok"}
        job.progress = 100
        job.status = "done"
        job.save()
        return

    job.status = "failed"
    job.error = "unsupported job kind"
    job.save()
