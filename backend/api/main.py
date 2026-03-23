from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.transactions import router as transaction_router
from backend.config.settings import settings
from database.connection.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="ML-ready Smart Budget Management APIs.",
    lifespan=lifespan,
)

app.include_router(transaction_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
