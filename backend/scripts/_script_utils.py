"""Shared helpers for backend maintenance scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Resolve backend package when executed as `python scripts/...py`
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import settings  # noqa: E402


def database_url() -> str:
    """Prefer 127.0.0.1 on Windows to avoid localhost resolution issues."""
    url = os.getenv("DATABASE_URL", str(settings.database_url))
    return url.replace("localhost", "127.0.0.1")


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}
