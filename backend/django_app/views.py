import logging

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from backend.django_app.models import CategoryMapping, RegexCategoryMapping
from backend.django_app.services.db_service import get_category_mappings, save_transactions, upsert_daily_summaries
from backend.django_app.services.fastapi_client import FastApiParseError, parse_pdf_with_fastapi

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
