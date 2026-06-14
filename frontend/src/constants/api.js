const djangoTarget = import.meta.env.VITE_DJANGO_URL || "http://127.0.0.1:8000";
const fastapiTarget = import.meta.env.VITE_FASTAPI_URL || "http://127.0.0.1:8001";

export const DJANGO_BASE_URL = import.meta.env.DEV ? "/django-api" : djangoTarget;
export const FASTAPI_BASE_URL = import.meta.env.DEV ? "/fastapi-api" : fastapiTarget;
export const DJANGO_TARGET_URL = djangoTarget;
export const FASTAPI_TARGET_URL = fastapiTarget;
