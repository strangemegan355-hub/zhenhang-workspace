"""No shipped credential: the retired default passwords must never come back.

The repository used to ship working passwords for the bootstrap administrator and all seven
trial accounts in scripts, docs, a sample CSV and two front-end bundles. This module is the guard
that keeps that decision from eroding: it scans the tracked source tree for the retired literals
and for password environment lookups that still carry a default.

Runs without a database.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-chars-long!!")

REPO_ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()

# Assembled from fragments so this file does not contain the strings it forbids.
RETIRED = [
    "Admin@" + "123456",
    "Trial@" + "Boss2026",
    "Trial@" + "Admin2026",
    "Trial@" + "Sales2026",
    "Trial@" + "Tech2026",
    "Trial@" + "Workshop2026",
    "Trial@" + "Finance2026",
    "Trial@" + "Approver2026",
]

SCAN_SUFFIXES = {
    ".py", ".ts", ".tsx", ".md", ".csv", ".yml", ".yaml", ".example", ".bat", ".ps1", ".sh",
}
SKIP_DIRS = {
    "node_modules", ".venv", ".git", ".next", "dist", "build", "__pycache__", ".pytest_cache",
    "volumes", "logs",
}
# A password read that supplies a non-empty fallback is exactly the pattern being retired. An
# empty fallback (`getenv("X_PASSWORD", "")`) is fine: it means "required, no default".
PASSWORD_ENV_DEFAULT = re.compile(
    r"getenv\(\s*[\"'][A-Za-z_]*PASSWORD[\"']\s*,\s*[\"'][^\"']+[\"']"
)


def _iter_source_files():
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in files:
            path = Path(root) / name
            if path.resolve() == SELF:
                continue
            # `.env.example` templates are covered by the ".example" suffix; a live, untracked
            # `.env` is deliberately out of scope so a developer's local file cannot fail CI.
            if path.suffix in SCAN_SUFFIXES:
                yield path


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def test_no_retired_default_password_literals():
    offenders: list[str] = []
    for path in _iter_source_files():
        text = _read(path)
        if text is None:
            continue
        if any(literal in text for literal in RETIRED):
            # Report the file without restating the credential.
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], "retired default password found in: " + ", ".join(sorted(set(offenders)))


def test_password_environment_lookups_have_no_default():
    offenders: list[str] = []
    for path in _iter_source_files():
        if path.suffix != ".py":
            continue
        text = _read(path)
        if text is None:
            continue
        for match in PASSWORD_ENV_DEFAULT.finditer(text):
            offenders.append(f"{path.relative_to(REPO_ROOT)}: {match.group(0)}")
    assert offenders == [], "password env lookup with a default: " + "; ".join(offenders)


def test_production_settings_refuse_shipped_defaults():
    from app.config.settings import Settings
    from pydantic import ValidationError

    base = {
        "secret_key": "a-real-production-secret-key-value-32chars",
        "database_url": "postgresql+psycopg://erp:erp@127.0.0.1:5432/erp_db",
        "redis_url": "redis://127.0.0.1:6379/0",
        "environment": "production",
    }
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **base, minio_access_key="minioadmin", minio_secret_key="minioadmin")

    accepted = Settings(
        _env_file=None,
        **base,
        minio_access_key="erp-minio",
        minio_secret_key="a-real-minio-secret-value",
    )
    assert accepted.environment == "production"


def test_development_keeps_the_local_compose_defaults():
    """Local development must still start with the documented compose defaults."""
    from app.config.settings import Settings

    dev = Settings(
        _env_file=None,
        secret_key="test-secret-key-min-32-chars-long!!",
        database_url="postgresql+psycopg://erp:erp@127.0.0.1:5432/erp_db",
        redis_url="redis://127.0.0.1:6379/0",
        environment="development",
    )
    assert dev.minio_secret_key == "minioadmin"


def test_sample_user_import_ships_placeholders_only():
    """Importing the sample CSV unchanged must not create an account with a usable password."""
    csv_path = REPO_ROOT / "backend" / "data" / "import_samples" / "users.csv"
    rows = [
        line
        for line in csv_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    header = rows[0].split(",")
    password_index = header.index("password")
    values = [row.split(",")[password_index] for row in rows[1:]]
    assert values, "expected at least one sample user row"
    for value in values:
        assert value == "set-a-real-password", f"sample row ships a usable password: {value!r}"


def test_importer_enforces_the_placeholder_rule():
    """Source-level assertion: the sample row above is only safe because the importer refuses it."""
    source = (
        REPO_ROOT / "backend" / "scripts" / "import_initial_master_data.py"
    ).read_text(encoding="utf-8")
    assert "PLACEHOLDER_PASSWORDS" in source
    assert "_validate_password(row[\"password\"]" in source
