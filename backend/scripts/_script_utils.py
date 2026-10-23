"""Shared helpers for backend maintenance scripts."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

# Resolve backend package when executed as `python scripts/...py`
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config.settings import settings  # noqa: E402

# Local trial / integration stack often listens here while backend/.env still says 5432.
INTEGRATION_PG_PORT = 55432
INTEGRATION_PG_HINT = (
    "postgresql+psycopg://erp:erp@127.0.0.1:55432/erp_db"
)


def database_url() -> str:
    """Prefer 127.0.0.1 on Windows to avoid localhost resolution issues."""
    url = os.getenv("DATABASE_URL", str(settings.database_url))
    return url.replace("localhost", "127.0.0.1")


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "是"}


def _parse_db_host_port(url: str) -> tuple[str, int]:
    """Return (host, port) from a SQLAlchemy or postgres URL."""
    raw = url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+asyncpg://", "postgresql://"
    )
    parsed = urlparse(raw)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 5432
    return host, port


def mask_database_url(url: str | None = None) -> str:
    """Host:port only — never print passwords."""
    url = url or database_url()
    host, port = _parse_db_host_port(url)
    return f"{host}:{port}"


def tcp_reachable(host: str, port: int, *, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def print_db_target(*, stream=None, probe: bool = True) -> str:
    """Print masked host:port; return the full ``database_url()`` for engines/guards.

    Callers (seed/setup) use the return value with ``create_engine`` / local-URL checks.
    Passwords are never printed — only ``host:port`` goes to the stream.
    """
    stream = stream or sys.stderr
    url = database_url()
    print(f"[db-target] DATABASE_URL → {mask_database_url(url)}", file=stream)
    if probe:
        warn_if_db_unreachable(stream=stream, already_printed=True)
    return url


def warn_if_db_unreachable(
    *,
    stream=None,
    probe_integration_fallback: bool = True,
    already_printed: bool = False,
) -> bool:
    """Probe DATABASE_URL TCP; warn with 55432 hint when default .env port is dead.

    Returns True if the configured target is reachable. Does **not** rewrite env or URLs.
    """
    stream = stream or sys.stderr
    url = database_url()
    host, port = _parse_db_host_port(url)
    if not already_printed:
        print(f"[db-target] DATABASE_URL → {mask_database_url(url)}", file=stream)
    if tcp_reachable(host, port):
        return True

    print(
        f"[db-target] WARN: {host}:{port} is not accepting TCP connections.",
        file=stream,
    )
    if (
        probe_integration_fallback
        and host in {"127.0.0.1", "localhost"}
        and port != INTEGRATION_PG_PORT
        and tcp_reachable("127.0.0.1", INTEGRATION_PG_PORT)
    ):
        print(
            f"[db-target] HINT: integration/trial Postgres appears open on 127.0.0.1:{INTEGRATION_PG_PORT}.",
            file=stream,
        )
        print(
            f'[db-target] HINT: set $env:DATABASE_URL="{INTEGRATION_PG_HINT}" '
            "(do not silently rewrite; .env may still say 5432).",
            file=stream,
        )
    return False


# Alias used by smoke_trial_login (API smoke; still surfaces the .env footgun).
warn_if_env_db_unreachable = warn_if_db_unreachable
