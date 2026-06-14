import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone

from backend.django_app.models import AccountCategoryMapping, CategoryMapping, RegexCategoryMapping
from backend.django_app.services.db_service import get_category_mappings, save_transactions, upsert_daily_summaries
from backend.django_app.services.fastapi_client import FastApiParseError, parse_pdf_with_fastapi
from backend.django_app.models import Transaction
from backend.fastapi_service.parser.categorizer import categorize_transaction, extract_upi_details
import re
from backend.django_app.models import ReparseJob
from django.shortcuts import get_object_or_404
import json

logger = logging.getLogger(__name__)


@require_GET
def health_check(_: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "service": "budgetiq-django"})


@require_GET
def list_category_mappings(_: HttpRequest) -> JsonResponse:
    return JsonResponse({"mappings": get_category_mappings()}, status=200)


@csrf_exempt
@require_POST
def create_category_mapping(request: HttpRequest) -> JsonResponse:
    keyword = str(request.POST.get("keyword", "")).strip().upper()
    category = str(request.POST.get("category", "")).strip().lower()

    if not keyword or not category:
        return JsonResponse({"error": "keyword and category are required"}, status=400)

    mapping, created = CategoryMapping.objects.get_or_create(
        keyword=keyword,
        defaults={"category": category},
    )

    if not created:
        mapping.category = category
        mapping.save(update_fields=["category"])

    return JsonResponse(
        {
            "id": mapping.id,
            "keyword": mapping.keyword,
            "category": mapping.category,
            "created": created,
        },
        status=201 if created else 200,
    )


@require_GET
def list_regex_mappings(_: HttpRequest) -> JsonResponse:
    rows = RegexCategoryMapping.objects.all().order_by("priority", "name")
    return JsonResponse(
        {
            "mappings": [
                {
                    "id": row.id,
                    "name": row.name,
                    "pattern": row.pattern,
                    "category": row.category,
                    "priority": row.priority,
                }
                for row in rows
            ]
        },
        status=200,
    )


@csrf_exempt
@require_POST
def create_regex_mapping(request: HttpRequest) -> JsonResponse:
    name = str(request.POST.get("name", "")).strip()
    pattern = str(request.POST.get("pattern", "")).strip()
    category = str(request.POST.get("category", "")).strip().lower()
    priority_raw = str(request.POST.get("priority", "100")).strip()

    if not name or not pattern or not category:
        return JsonResponse({"error": "name, pattern and category are required"}, status=400)

    try:
        priority = int(priority_raw)
    except ValueError:
        return JsonResponse({"error": "priority must be an integer"}, status=400)

    mapping, created = RegexCategoryMapping.objects.get_or_create(
        name=name,
        defaults={"pattern": pattern, "category": category, "priority": priority},
    )

    if not created:
        mapping.pattern = pattern
        mapping.category = category
        mapping.priority = priority
        mapping.save(update_fields=["pattern", "category", "priority"])

    return JsonResponse(
        {
            "id": mapping.id,
            "name": mapping.name,
            "pattern": mapping.pattern,
            "category": mapping.category,
            "priority": mapping.priority,
            "created": created,
        },
        status=201 if created else 200,
    )


@require_GET
def list_account_mappings(_: HttpRequest) -> JsonResponse:
    rows = AccountCategoryMapping.objects.all().order_by("priority", "upi_id")
    return JsonResponse(
        {
            "mappings": [
                {
                    "id": row.id,
                    "upi_id": row.upi_id,
                    "name": row.name,
                    "category": row.category,
                    "priority": row.priority,
                }
                for row in rows
            ]
        },
        status=200,
    )


@csrf_exempt
@require_POST
def create_account_mapping(request: HttpRequest) -> JsonResponse:
    upi_id = str(request.POST.get("upi_id", "")).strip()
    name = str(request.POST.get("name", "")).strip().upper()
    category = str(request.POST.get("category", "")).strip().lower()
    priority_raw = str(request.POST.get("priority", "1")).strip()

    if not upi_id or not category:
        return JsonResponse({"error": "upi_id and category are required"}, status=400)

    try:
        priority = int(priority_raw)
    except ValueError:
        return JsonResponse({"error": "priority must be an integer"}, status=400)

    mapping, created = AccountCategoryMapping.objects.get_or_create(
        upi_id=upi_id,
        name=name,
        defaults={"category": category, "priority": priority},
    )

    if not created:
        mapping.category = category
        mapping.priority = priority
        mapping.save(update_fields=["category", "priority"])

    return JsonResponse(
        {
            "id": mapping.id,
            "upi_id": mapping.upi_id,
            "name": mapping.name,
            "category": mapping.category,
            "priority": mapping.priority,
            "created": created,
        },
        status=201 if created else 200,
    )


@csrf_exempt
@require_POST
def upload_pdf(request: HttpRequest) -> JsonResponse:
    pdf_file = request.FILES.get("file")
    password = request.POST.get("password")

    if pdf_file is None:
        return JsonResponse({"error": "Missing file in multipart form-data"}, status=400)

    if not pdf_file.name.lower().endswith(".pdf"):
        return JsonResponse({"error": "Only PDF files are supported"}, status=400)

    mappings = get_category_mappings()

    try:
        parsed = parse_pdf_with_fastapi(
            file_name=pdf_file.name,
            file_bytes=pdf_file.read(),
            password=password,
            mappings=mappings,
        )
    except FastApiParseError as exc:
        return JsonResponse({"error": str(exc)}, status=502)

    transactions = parsed.get("transactions", [])
    summaries = parsed.get("summaries", [])

    if not transactions:
        return JsonResponse({"message": "No transactions extracted", "transactions": [], "summaries": []}, status=200)

    saved = save_transactions(transactions=transactions, source_file=pdf_file.name)
    upsert_daily_summaries(summaries=summaries)

    logger.info("Processed file=%s tx_count=%s summary_count=%s", pdf_file.name, len(transactions), len(summaries))

    return JsonResponse(
        {
            "message": "PDF processed successfully",
            "saved_transactions": len(saved),
            "transactions": transactions,
            "summaries": summaries,
        },
        status=201,
    )


@csrf_exempt
@require_POST
def reparse_mapping(request: HttpRequest) -> JsonResponse:
    """Re-apply a mapping to existing transactions.

    POST params expected:
      - kind: 'keyword'|'regex'|'account'
      - category: target category
      - keyword (when kind=keyword)
      - pattern (when kind=regex)
      - upi_id (when kind=account)

    This endpoint updates matching Transaction rows in batches and
    returns the number of rows updated.
    """
    kind = str(request.POST.get("kind", "")).strip().lower()
    category = str(request.POST.get("category", "other")).strip().lower() or "other"

    if kind == "all":
        keyword_map = {
            str(row.keyword).strip().upper(): str(row.category).strip().lower()
            for row in CategoryMapping.objects.all()
            if str(row.keyword).strip()
        }
        regex_rules = [
            (re.compile(str(row.pattern), re.IGNORECASE), str(row.name).strip(), str(row.category).strip().lower(), int(row.priority or 100))
            for row in RegexCategoryMapping.objects.all()
            if str(row.pattern).strip()
        ]
        regex_rules.sort(key=lambda item: item[3])
        account_rules = [
            {
                "upi_id": str(row.upi_id).strip().upper(),
                "name": str(row.name).strip().upper(),
                "category": str(row.category).strip().lower(),
                "priority": int(row.priority or 1),
            }
            for row in AccountCategoryMapping.objects.all()
        ]
        account_rules.sort(key=lambda item: int(item["priority"]))

        updated = 0
        for tx in Transaction.objects.all().only("id", "description").iterator(chunk_size=500):
            tx_category, tx_source, confidence, _ = categorize_transaction(
                tx.description or "",
                keyword_map,
                regex_rules,
                account_rules,
            )
            Transaction.objects.filter(id=tx.id).update(
                category=tx_category,
                category_source=tx_source,
                confidence=confidence,
            )
            updated += 1

        return JsonResponse(
            {
                "updated": updated,
                "status": "done",
                "updated_at": timezone.now().isoformat(),
            },
            status=200,
        )

    if kind == "keyword":
        keyword = str(request.POST.get("keyword", "")).strip()
        if not keyword:
            return JsonResponse({"error": "keyword is required for kind=keyword"}, status=400)
        qs = Transaction.objects.filter(description__icontains=keyword)
        updated = qs.update(category=category, category_source="keyword", confidence=1.0)
        return JsonResponse({"updated": updated}, status=200)

    if kind == "regex":
        pattern = str(request.POST.get("pattern", "")).strip()
        if not pattern:
            return JsonResponse({"error": "pattern is required for kind=regex"}, status=400)
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return JsonResponse({"error": "invalid regex pattern"}, status=400)

        # Iterate transaction descriptions in manageable batches, collect IDs to update
        batch_size = 1000
        ids_to_update = []
        qs = Transaction.objects.all().values_list("id", "description")
        for tid, desc in qs.iterator():
            if compiled.search(str(desc or "")):
                ids_to_update.append(tid)
            if len(ids_to_update) >= batch_size:
                Transaction.objects.filter(id__in=ids_to_update).update(category=category, category_source="regex", confidence=1.0)
                ids_to_update = []

        if ids_to_update:
            Transaction.objects.filter(id__in=ids_to_update).update(category=category, category_source="regex", confidence=1.0)

        # count updated rows — simple heuristic: number of matched ids
        return JsonResponse({"updated": "ok"}, status=200)

    if kind == "account":
        upi_id = str(request.POST.get("upi_id", "")).strip()
        if not upi_id:
            return JsonResponse({"error": "upi_id is required for kind=account"}, status=400)

        # Scan transactions and match extracted UPI IDs
        batch_size = 1000
        ids_to_update = []
        qs = Transaction.objects.all().values_list("id", "description")
        for tid, desc in qs.iterator():
            details = extract_upi_details(str(desc or ""))
            if details.get("upi_id") and details.get("upi_id").upper() == upi_id.upper():
                ids_to_update.append(tid)
            if len(ids_to_update) >= batch_size:
                Transaction.objects.filter(id__in=ids_to_update).update(category=category, category_source="account_rule", confidence=1.0)
                ids_to_update = []
        if ids_to_update:
            Transaction.objects.filter(id__in=ids_to_update).update(category=category, category_source="account_rule", confidence=1.0)

        return JsonResponse({"updated": "ok"}, status=200)

    return JsonResponse({"error": "unsupported kind"}, status=400)


@csrf_exempt
@require_POST
def enqueue_reparse(request: HttpRequest) -> JsonResponse:
    """Create a ReparseJob and return job id. Expects same POST params as reparse_mapping."""
    kind = str(request.POST.get("kind", "")).strip().lower()
    category = str(request.POST.get("category", "other")).strip().lower() or "other"
    params = {"category": category}
    if kind == "all":
        job = ReparseJob.objects.create(kind=kind, params=params, status="queued", progress=0)
        return JsonResponse({"job_id": job.id}, status=201)

    if kind == "keyword":
        keyword = str(request.POST.get("keyword", "")).strip()
        if not keyword:
            return JsonResponse({"error": "keyword required"}, status=400)
        params["keyword"] = keyword
    elif kind == "regex":
        pattern = str(request.POST.get("pattern", "")).strip()
        if not pattern:
            return JsonResponse({"error": "pattern required"}, status=400)
        params["pattern"] = pattern
    elif kind == "account":
        upi_id = str(request.POST.get("upi_id", "")).strip()
        if not upi_id:
            return JsonResponse({"error": "upi_id required"}, status=400)
        params["upi_id"] = upi_id
    else:
        return JsonResponse({"error": "unsupported kind"}, status=400)

    job = ReparseJob.objects.create(kind=kind, params=params, status="queued", progress=0)
    return JsonResponse({"job_id": job.id}, status=201)


@require_GET
def reparse_status(request: HttpRequest, job_id: int) -> JsonResponse:
    job = get_object_or_404(ReparseJob, id=job_id)
    return JsonResponse({
        "id": job.id,
        "status": job.status,
        "progress": job.progress,
        "result": job.result,
        "error": job.error,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    })
