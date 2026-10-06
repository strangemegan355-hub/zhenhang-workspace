"""A reviewed inventory keyed by a file or module must say **why** each entry is correct.

Rounds 192, 193 and 208 each corrected a record that was **true but missing its reason**:

* `app/models/__init__.py` was noted as "imported by nothing" — `alembic/env.py` imports it, with the comment
  *"registers metadata"*;
* "only `Tenant` carries `AuditSoftDeleteMixin`" — about sixty models do; the note generalised a **five-model sample**;
* `business:approval:read` was recorded as "seeded but no route requires it" — true, and it is a **live menu-visibility
  gate**, so the note read as dead weight.

**Each was a seed for the next misreading.** The convention this suite already follows is that a reviewed entry carries
the reason it is correct — measured in round 209: **seven reviewed inventories, 56 entries, every one reasoned.**

**Three dictionaries are exempt by shape, not by name**: `SURFACES` (`{"roles": "/api/v1/roles"}`), `REQUIRED_HEADERS`
(`{"X-Frame-Options": "DENY"}`) and `SCOPED_DOCUMENTS` (`{"accounting": "AccountingEntry"}`) are **data maps whose values
are values**. The rule below therefore keys off the **key shape** — a key containing `/` or ending in `.py` names a file or
module, so its value has to be a reason.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTS = [*(REPO / "backend" / "tests").glob("*.py"), *(REPO / "backend" / "integration_tests").glob("*.py")]

# A value shorter than this is a label rather than a reason. Measured: the shortest real reason in round 209's survey was
# comfortably above it, and the exemptions above are excluded by key shape before this is consulted.
MINIMUM_REASON = 20
PLACEHOLDERS = {"todo", "n/a", "-", "", "ok", "none", "see above"}


def _path_keyed_dicts() -> list[tuple[str, str, list[tuple[str, str]]]]:
    found: list[tuple[str, str, list[tuple[str, str]]]] = []
    for path in sorted(TESTS):
        source = path.read_text(encoding="utf-8", errors="replace")
        for node in ast.parse(source).body:
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id for t in targets if isinstance(t, ast.Name)]
            value = node.value
            if not names or not isinstance(value, ast.Dict) or not value.keys:
                continue
            entries: list[tuple[str, str]] = []
            for key, val in zip(value.keys, value.values):
                if not (isinstance(key, ast.Constant) and isinstance(key.value, str)):
                    continue
                if not (isinstance(val, ast.Constant) and isinstance(val.value, str)):
                    continue
                entries.append((key.value, val.value))
            if entries and any("/" in key or key.endswith(".py") for key, _ in entries):
                found.append((path.relative_to(REPO).as_posix(), names[0], entries))
    return found


def test_the_scan_finds_the_reviewed_inventories():
    inventories = _path_keyed_dicts()
    assert len(inventories) >= 5, (
        f"only {len(inventories)} path-keyed reviewed dictionaries were found, so the scan is not seeing the suite"
    )
    total = sum(len(entries) for _, _, entries in inventories)
    assert total >= 30, f"only {total} reviewed entries were found across them"


def test_every_reviewed_entry_says_why_it_is_correct():
    offenders: list[str] = []
    for relative, name, entries in _path_keyed_dicts():
        for key, reason in entries:
            text = reason.strip()
            if len(text) < MINIMUM_REASON or text.lower() in PLACEHOLDERS or text == key:
                offenders.append(f"{relative}: {name}[{key!r}] = {reason!r}")

    assert offenders == [], (
        "these reviewed entries name something without saying why it is correct. **A record that is true but omits its "
        "reason is how rounds 192, 193 and 208 each produced a later misreading** — add the reason, or move the entry to "
        "a data map if its value is a value rather than a justification:\n  " + "\n  ".join(offenders)
    )
