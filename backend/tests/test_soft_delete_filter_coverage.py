"""Every hand-written query on a soft-deletable model must carry the `is_deleted` predicate.

Round 194 measured the architecture: `common_repository.paginate_query` and `get_by_id` apply
`model.is_deleted.is_(False)` **unconditionally**, `core/data_scope.py` combines the soft-delete predicate with the
data-scope predicate in one function, and models without the column (`Role`, `Permission`, `Department`, `User`) bypass
the helper deliberately — which `admin_repository.py`'s comment records.

**The leak class is a hand-written query that forgets the predicate**, and round 92 built
`test_repository_predicate_coverage.py` for the sibling question about the *data-scope* predicate. This is the
soft-delete half.

**The first version of the measuring probe reported ten offenders and all ten were false positives**, because it looked
only at the `select`'s own statement while every one of them passed a `filters` list built earlier in the function. That
is why this test **tracks `filters`-style names within the enclosing function** — and why the reading of the ten, not
the count, is what settled it.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import pytest  # noqa: E402


def _soft_delete_models() -> set[str]:
    import app.models  # noqa: F401 - registers the metadata, as `alembic/env.py` does
    from app.models import Base

    for module in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module(f"app.models.{module.name}")

    return {
        mapper.class_.__name__
        for mapper in Base.registry.mappers
        if "is_deleted" in {column.name for column in mapper.columns}
    }


def _repository_files() -> list[Path]:
    roots = [BACKEND / "app" / "repositories", *(BACKEND / "app" / "domains").glob("*/repositories")]
    return sorted(p for root in roots if root.is_dir() for p in root.rglob("*.py"))


def _names_carrying_the_predicate(function: ast.AST, source_lines: list[str]) -> set[str]:
    """Local names whose list ends up containing an `is_deleted` condition.

    Two shapes occur in this codebase and **the first version only handled the second**, which is why it reported 66
    offenders instead of the real number:

        filters = [Model.is_deleted.is_(False)]      # assigned with the predicate present
        filters = []
        filters.append(Model.is_deleted.is_(False))  # built up afterwards — the common shape

    So a name qualifies when any statement that mentions it — assignment or `.append(...)`/`.extend(...)`/`+=` — also
    mentions `is_deleted` within the same statement.
    """
    names: set[str] = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.stmt):
            continue
        end = getattr(node, "end_lineno", node.lineno)
        fragment = "\n".join(source_lines[node.lineno - 1 : end])
        if "is_deleted" not in fragment:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                names.add(child.id)
    return names


def _scans_missing_the_predicate(path: Path, soft: set[str]) -> list[str]:
    source = path.read_text(encoding="utf-8", errors="replace")
    lines = source.splitlines()
    tree = ast.parse(source)
    offenders: list[str] = []

    for function in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        carrying = _names_carrying_the_predicate(function, lines)
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name != "select":
                continue
            target = next((a.id for a in node.args if isinstance(a, ast.Name) and a.id in soft), None)
            if target is None:
                continue

            # **The span has to be the enclosing STATEMENT, not the `select` call.** A chained, parenthesised statement
            #
            #     stmt = (
            #         select(AccountingEntry)
            #         .where(AccountingEntry.id == entry_id, AccountingEntry.is_deleted.is_(False))
            #     )
            #
            # gives the call an `end_lineno` on its own line, so looking at the call alone misses the predicate on the
            # next one — which is how the first version reported 66 offenders that were all false positives.
            span = node
            for candidate in ast.walk(function):
                if isinstance(candidate, ast.stmt) and candidate.lineno <= node.lineno <= getattr(
                    candidate, "end_lineno", candidate.lineno
                ):
                    if getattr(candidate, "end_lineno", 0) >= getattr(span, "end_lineno", 0):
                        span = candidate
            fragment = "\n".join(lines[span.lineno - 1 : getattr(span, "end_lineno", span.lineno)])

            if "is_deleted" in fragment:
                continue
            # A `.where(*filters)` or `.where(*some_list)` whose list carried the predicate counts.
            if any(f"*{carried}" in fragment for carried in carrying):
                continue
            offenders.append(f"{path.relative_to(BACKEND).as_posix()}:{node.lineno}  select({target})")
    return offenders


def test_the_scan_finds_the_soft_deletable_models_and_the_repositories():
    soft = _soft_delete_models()
    assert len(soft) >= 50, f"only {len(soft)} models declare is_deleted, so the model import is incomplete"
    for expected in ("Quote", "Project", "Customer", "AfterSalesServiceRequest"):
        assert expected in soft, f"{expected} is not seen as soft-deletable"
    # The four surfaces that deliberately bypass the helper have no such column.
    for absent in ("Role", "Permission", "Department", "User"):
        assert absent not in soft, f"{absent} now declares is_deleted, so the bypass recorded in admin_repository changed"

    files = _repository_files()
    assert len(files) >= 15, f"only {len(files)} repository files were found"


def test_every_repository_scan_carries_the_soft_delete_predicate():
    soft = _soft_delete_models()
    offenders: list[str] = []
    for path in _repository_files():
        offenders.extend(_scans_missing_the_predicate(path, soft))
    assert offenders == [], (
        "these repository queries scan a soft-deletable model without excluding deleted rows, so a deleted record "
        "would still be returned:\n  " + "\n  ".join(offenders)
    )
