"""The complement of round 171's guard: every filesystem walk is filtered, however it is written.

`test_guard_scopes.py` checks that each `SKIP`-like constant covers the directories its file's walk can reach. **A file
that walks the tree and writes no such constant is invisible to it** — round 199's rule ("a guard triggered by *somewhere
in this file* cannot see *nowhere in this file*") applied to the guard built in round 171.

Round 200 measured 24 test files that walk the filesystem. **Eight define a skip constant — exactly round 171's set — and
the other three real walks filter inline**, each naming the hostile directories it can actually meet:

* `test_module_reachability.py:89` — `"__pycache__" in path.parts or ".venv" in path.parts`, walking `backend/`;
* `test_no_unsafe_rendering.py:58` — `node_modules`, `dist`, `.next`, `build`, walking `apps/`;
* `test_route_frontend_alignment.py:129` — `node_modules`, `dist`, `.next`, walking `apps/` and `packages/`.

The rest of the 24 are `ast.walk` calls, which are not filesystem walks at all — **the first version of the measuring
probe conflated the two**, which is why this guard parses calls rather than matching the word "walk".
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTS = [*(REPO / "backend" / "tests").glob("*.py"), *(REPO / "backend" / "integration_tests").glob("*.py")]

# Directory names no scan in this repository should descend into, and the reason this list is not empty: `node_modules`
# exists at the repository root and contains three `.py` files, and `.venv` holds the interpreter.
HOSTILE = {"node_modules", ".venv", "__pycache__", ".next", "dist", "build", "site-packages"}

SKIP_CONST = re.compile(r"^\s*[A-Z_]*(?:SKIP|IGNORE|EXCLUDE)[A-Z_]*\s*[:=]", re.MULTILINE)

# Reviewed in round 200: walkers the inline filter check does not catch, each with the reason its root cannot reach a
# hostile directory. **The four that filter `path.parts` inline are deliberately NOT here** — the check above catches
# them, and listing them made this guard report its own record as stale, which is the second direction working.
NARROW_ROOTS: dict[str, str] = {
    "test_authz_auditor_has_teeth.py": "globs `app/api/v1/endpoints/*.py`, a flat directory",
    "test_data_scope_coverage.py": "globs the endpoint, service and domain directories, each flat",
    "test_database_baseline.py": "globs `app/models/*.py`, a flat directory",
    "test_guard_scopes.py": "globs `backend/tests/*.py`, a flat directory",
    "test_hook_route_alignment.py": "walks the hook source tree only, `packages/query-hooks/src`",
    "test_page_data_use.py": "walks the app-router page tree only",
    "test_repository_predicate_coverage.py": "globs `app/repositories/*.py`, a flat directory",
    "test_scope_coverage.py": "walks `app/` for `*.py`; `__pycache__` holds only `.pyc`, so the glob finds nothing there",
}


def _filesystem_walks(tree: ast.AST) -> list[int]:
    """Line numbers of `.rglob(...)`/`.glob(...)` calls — **not `ast.walk`**, which walks an in-memory tree."""
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"rglob", "glob"}:
            lines.append(node.lineno)
    return sorted(lines)


def test_the_scan_finds_the_test_suite_and_its_walks():
    assert len(TESTS) >= 60, f"only {len(TESTS)} test files were found"
    walkers = [p for p in TESTS if _filesystem_walks(ast.parse(p.read_text(encoding="utf-8", errors="replace")))]
    # Both directions: the set is neither empty nor everything.
    assert len(walkers) >= 15, f"only {len(walkers)} test files walk the filesystem, so the scan is broken"
    assert len(walkers) <= len(TESTS), "more walkers than files"


def test_every_filesystem_walk_is_filtered_somehow():
    """Either a skip constant exists, or the file names the hostile directories inline."""
    unfiltered: list[str] = []
    exempted: set[str] = set()
    for path in TESTS:
        source = path.read_text(encoding="utf-8", errors="replace")
        walks = _filesystem_walks(ast.parse(source))
        if not walks:
            continue
        if SKIP_CONST.search(source):
            continue
        # An inline filter, in the shape this repository actually uses: a membership test against `path.parts` naming a
        # hostile directory, e.g. `if "node_modules" in path.parts` or `any(part in {...} for part in path.parts)`.
        named = [name for name in HOSTILE if name in source]
        # The shape must not be tied to the variable's name: the files here use both `path.parts` and `p.parts`, and the
        # first version's `path\.parts` therefore missed three of them.
        if named and (re.search(r"\.parts", source) or re.search(r"part\s+in\s*\{", source)):
            continue
        # Otherwise the file is one whose walk this guard has reviewed as unable to reach a hostile directory. Collected
        # separately so the record is asserted in both directions: an unrecorded walker fails, and a recorded one that
        # stops needing the exemption is reported as stale.
        if path.name in NARROW_ROOTS:
            exempted.add(path.name)
            continue
        unfiltered.append(f"{path.relative_to(REPO).as_posix()}  walks at lines {walks}")

    stale = sorted(set(NARROW_ROOTS) - exempted)
    assert stale == [], (
        "these files are recorded as narrow-root walkers but no longer need the exemption — they either stopped walking "
        f"or now filter on their own, so the record is stale: {stale}"
    )
    assert unfiltered == [], (
        "these test files walk the filesystem without excluding the directories this repository fills with other "
        "people's code:\n  " + "\n  ".join(unfiltered) + "\n"
        "Add a SKIP-style constant (round 171's pattern), filter `path.parts` inline, or record the root here **with the "
        "reason it cannot reach a hostile directory**."
    )
