from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def generate_artifact_version() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"v{timestamp}-{uuid4().hex[:8]}"


def build_versioned_path(base_path: Path, version: str) -> Path:
    return base_path.with_name(f"{base_path.stem}.{version}{base_path.suffix}")


def build_manifest_path(base_path: Path) -> Path:
    return base_path.with_name(f"{base_path.stem}.manifest.json")


def read_manifest(base_path: Path) -> dict[str, Any] | None:
    manifest_path = build_manifest_path(base_path)
    if not manifest_path.exists():
        return None

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    return payload if isinstance(payload, dict) else None


def write_manifest(manifest_path: Path, payload: dict[str, Any]) -> None:
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def resolve_artifact_paths(model_path: Path, vectorizer_path: Path) -> tuple[Path, Path]:
    manifest = read_manifest(model_path)
    if not manifest:
        return model_path, vectorizer_path

    model_candidate = Path(manifest.get("model_path", model_path))
    vectorizer_candidate = Path(manifest.get("vectorizer_path", vectorizer_path))

    if model_candidate.exists() and vectorizer_candidate.exists():
        return model_candidate, vectorizer_candidate

    return model_path, vectorizer_path