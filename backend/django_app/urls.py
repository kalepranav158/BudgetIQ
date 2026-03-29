from django.urls import path

from backend.django_app.views import (
    create_category_mapping,
    health_check,
    list_category_mappings,
    upload_pdf,
)

urlpatterns = [
    path("health", health_check, name="health"),
    path("category-mapping", list_category_mappings, name="list-category-mapping"),
    path("category-mapping/create", create_category_mapping, name="create-category-mapping"),
    path("upload-pdf", upload_pdf, name="upload-pdf"),
]
