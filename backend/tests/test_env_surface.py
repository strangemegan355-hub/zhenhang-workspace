"""Every declared env variable must have a reader, and every settings field a consumer.

Round 80 removed two dead keys (`REALTIME_PUBLIC_BASE_URL`, `WORKER_REPLICAS`) because nothing referenced them
anywhere. Round 97 asked the question systematically and the answer was clean — 55 declarations, all read; 29
settings fields, all consumed — but only after four of my own measurement errors dissolved:

* a **suffix** filter excluded `backend/.env.example`, whose suffix is `.example`, and reported **0 declarations**;
* a **case-sensitive** search reported **17 unread**, because pydantic-settings maps `ACCESS_TOKEN_EXPIRE_MINUTES`
  onto the field `access_token_expire_minutes`;
* a **negative lookbehind for `.`** excluded `settings.<field>`, the very access pattern being looked for, and
  reported **16 unused fields**;
* a spot-check used `Select-String -Recurse` (not a parameter) and reported **0 readers** for fields that have
  them.

Every one of those numbers looked plausible and was wrong. So this test carries the two design choices those
errors taught — match case-insensitively, and allow a leading dot — plus a vacuity guard on each half, because
error one is exactly what a silently empty filter looks like.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SETTINGS = "backend/app/config/settings.py"
SKIP_PARTS = {"node_modules", ".next", "dist", ".venv", "site-packages", "__pycache__", ".git"}
TEXT_SUFFIXES = {".md", ".json", ".yml", ".yaml", ".sh", ".ps1", ".py", ".mjs", ".js", ".ts", ".tsx"}
ASSIGNMENT = re.compile(r"^\s*#?\s*([A-Z][A-Z0-9_]{2,})\s*=")


def _tracked_texts() -> dict[str, str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    texts: dict[str, str] = {}
    for relative in (rel for rel in result.stdout.split("\0") if rel.strip()):
        # By name as well as by suffix: `backend/.env.example` has suffix `.example`.
        is_env = Path(relative).name.startswith(".env") or Path(relative).name.endswith(".env.example")
        if Path(relative).suffix not in TEXT_SUFFIXES and not is_env:
            continue
        if SKIP_PARTS & set(Path(relative).parts):
            continue
        path = REPO / relative
        if path.is_file():
            texts[relative] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def _env_files(texts: dict[str, str]) -> list[str]:
    return [rel for rel in texts if Path(rel).name.startswith(".env") or Path(rel).name.endswith(".env.example")]


def test_every_declared_env_variable_is_read_somewhere():
    texts = _tracked_texts()
    env_files = _env_files(texts)
    assert env_files, "no env file was found, so this check would pass vacuously"

    declared: set[str] = set()
    for rel in env_files:
        for line in texts[rel].splitlines():
            match = ASSIGNMENT.match(line)
            if match:
                declared.add(match.group(1))

    # A guard against error one: a filter that silently finds nothing.
    assert len(declared) >= 20, f"expected the env files to declare many variables, found {len(declared)}"

    unread = []
    for key in sorted(declared):
        # Case-insensitively (error two) and allowing a leading dot for `settings.<field>` (error three).
        pattern = re.compile(rf"\b{re.escape(key)}\b", re.IGNORECASE)
        readers = [rel for rel in texts if rel not in env_files and pattern.search(texts[rel])]
        if not readers:
            unread.append(key)

    assert unread == [], (
        "these variables are declared but nothing reads them, so setting one would do nothing:\n"
        + "\n".join(f"    {key}" for key in unread)
    )


def test_every_settings_field_is_used_outside_settings():
    texts = _tracked_texts()
    settings_text = texts.get(SETTINGS)
    assert settings_text, f"{SETTINGS} was not found"
    fields = re.findall(r"^    (\w+)\s*:[^=\n]*=", settings_text, re.MULTILINE)
    assert len(fields) >= 20, f"expected many settings fields, found {len(fields)}"

    others = {rel: text for rel, text in texts.items() if rel != SETTINGS}
    unused = []
    for field in fields:
        pattern = re.compile(rf"\b{re.escape(field)}\b")
        if not any(pattern.search(text) for text in others.values()):
            unused.append(field)

    assert unused == [], (
        "these settings fields are declared and referenced nowhere else, so the variable behind them "
        "configures nothing:\n" + "\n".join(f"    {field}" for field in unused)
    )
