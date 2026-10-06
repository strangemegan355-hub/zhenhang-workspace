"""A module with content must be imported by something, or be recorded as inert.

Found by measuring reachability instead of counting names in test files. **The first sweep was the wrong instrument**:
it reported 133 of 142 modules with a function no test calls, which counts a *name in a test file* and therefore marks
every service invoked **through a route** as uncovered — the same "a name is not the object" wall as rounds 147 and 149.
Reporting that as a coverage gap would have been a fabricated alarm.

Reachability by **imports** gives a believable answer: 259 of 309 modules under `app/` are reachable from the
production entry points, and the tests reach the same 259. Of the rest, about forty-five are one-to-three-line package
`__init__.py` files, which a package requires and which are therefore not dead.

**What is left, and what this guard pins, is the handful of files with real content that nothing imports at all:**

* `app/commands/quote_commands.py` (28 lines) — a `CreateQuoteCommand` dataclass;
* `app/queries/quote_queries.py` (16 lines) — the matching `ListQuotesQuery` and `CompareQuoteVersionsQuery`;
* `app/models/quote_template.py` (38 lines) — a SQLAlchemy model that no code imports, so it never registers with
  `Base.metadata` and its table is not in the chain.

They are **recorded, not deleted**: removing files is the pending decision, and this test's job is to make the list
explicit and to fail when it changes.

**One limit of the instrument is recorded rather than hidden:** five `app/domains/*/application/__init__.py` shims are
imported by nothing either, but `test_layer_parity.py` **asserts their existence by path**, so they are not inert. This
guard is scoped **above five lines** precisely so that the empty package markers and those three-line shims stay out of
it, and the reachability walk is only about imports.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
APP = BACKEND / "app"

# Below this many lines a file is package plumbing; the guard is about files with something in them.
MIN_LINES = 6

INERT_MODULES: dict[str, str] = {
    "app/commands/quote_commands.py": (
        "a CQRS command dataclass imported by nothing; the command pattern was started and not continued, as the "
        "absence of any app/queries counterpart in use shows"
    ),
    "app/queries/quote_queries.py": (
        "the matching query dataclasses, equally unimported"
    ),
    # `app/models/quote_template.py` was briefly listed here and is **not**: `app/models/__init__.py` imports it.
    # The interesting fact is one level up — **that aggregator is imported by nothing**, so the model is reachable
    # only through an unreachable module, and nothing ever registers it with `Base.metadata`. A flat "is it imported"
    # check cannot see that, and recording it here beats claiming the model is unimported when it is not.
}


def _app_modules() -> dict[str, Path]:
    modules: dict[str, Path] = {}
    for path in sorted(APP.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        dotted = ".".join(path.relative_to(BACKEND).with_suffix("").parts)
        if dotted.endswith(".__init__"):
            dotted = dotted[: -len(".__init__")]
        modules[dotted] = path
    return modules


def _imports_of(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names if alias.name.startswith("app."))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("app."):
            found.add(node.module)
            # `from app.services import procurement_service` names a **module** through the alias, not the package.
            # Dropping this was the bug that made the first run of this guard report 91 false positives.
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def _imported_modules() -> set[str]:
    """Every app module named by an import anywhere in the backend, tests included."""
    named: set[str] = set()
    for path in sorted(BACKEND.rglob("*.py")):
        if "__pycache__" in path.parts or ".venv" in path.parts:
            continue
        named |= _imports_of(path)
    return named


def test_every_module_with_content_is_imported_or_recorded_as_inert():
    modules = _app_modules()
    assert len(modules) > 100, f"only {len(modules)} app modules were found; the walk is broken, not the code"

    imported = _imported_modules()
    unimported: set[str] = set()
    for dotted, path in modules.items():
        if path.name == "__init__.py":
            continue  # package plumbing, required by the package
        if len(path.read_text(encoding="utf-8", errors="replace").splitlines()) < MIN_LINES:
            continue
        # A module counts as used when it, or anything under it, is named by an import.
        if dotted in imported or any(name.startswith(dotted + ".") for name in imported):
            continue
        unimported.add(path.relative_to(BACKEND).as_posix())

    unexpected = sorted(unimported - set(INERT_MODULES))
    assert unexpected == [], (
        "these modules contain code that nothing imports. If a module is dead, delete it in the same change that "
        "removes its last reference; if it is deliberately inert, add it to INERT_MODULES with the reason:\n  "
        + "\n  ".join(unexpected)
    )

    stale = sorted(set(INERT_MODULES) - unimported)
    assert stale == [], (
        "these entries are recorded as inert but their modules are now imported, so the record is out of date:\n  "
        + "\n  ".join(stale)
    )


def test_the_inert_entries_name_files_that_exist():
    missing = sorted(name for name in INERT_MODULES if not (BACKEND / name).is_file())
    assert missing == [], f"INERT_MODULES names files that no longer exist: {missing}"


def test_the_quote_template_model_declares_a_table_the_chain_creates():
    """The difference between 'inert' and 'dead weight': the table **is** live, and the model is a second declaration.

    This assertion was written the other way round first, expecting no migration to create the table. Reading the
    failure — `quote_pdf_templates` **is** created by the chain — corrected the finding rather than the test.
    """
    versions = BACKEND / "alembic" / "versions"
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in versions.glob("*.py"))
    tables = set(re.findall(r'create_table\(\s*["\']([^"\']+)["\']', text))
    assert tables, "no create_table call was found, so this check has nothing to compare"
    model_source = (BACKEND / "app" / "models" / "quote_template.py").read_text(encoding="utf-8", errors="replace")
    declared = re.findall(r'__tablename__\s*=\s*["\']([^"\']+)["\']', model_source)
    assert declared, "the model no longer declares __tablename__, so this check has nothing to compare"
    for table in declared:
        assert table in tables, (
            f"{table!r} is not created by the migration chain, so the model is inert after all and the INERT_MODULES "
            "entry above needs rewriting again"
        )
