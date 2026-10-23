"""A guard that walks the repository root must skip `node_modules`.

Measured in round 171: `backend/tests` holds **eight** skip-set constants with **twelve** distinct members, and they
disagree — `node_modules` is in six, `.pytest_cache` in three, `htmlcov` and `logs` in one each. The obvious worry is a
guard reading dependency code, and it is a real one: **`node_modules` exists at the repository root and contains three
`.py` files** (`flatted/python/flatted.py`). `test_duplicate_code.py` decides by comparing function bodies, so a
dependency's code entering its scan could produce a false positive.

**Measuring the two guards with the minimal set `{.venv, __pycache__}` settles it: both walk `backend/app`, not the
repository root** — `test_duplicate_code.py` and `test_page_items_validation.py` glob under `APP`. **So their small sets
are correct rather than lax, and the size of a skip set is not the invariant. The invariant is the pairing: a walk root
and the set that covers it.**

That is what this pins, and it is derived rather than listed: each test file's `rglob` patterns and roots are parsed from
its own source, and **only a file that walks the repository root is required to skip `node_modules`**. A guard moved to a
wider root without widening its set fails here, which is the mistake this exists to prevent.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "backend" / "tests"

# The directory that makes a repository-root walk unsafe: it exists, and it contains source files this project did not
# write.
HOSTILE_AT_ROOT = "node_modules"

# Files whose `rglob` roots are not the repository root, with the reason. Asserted in both directions: a file here whose
# source stops matching is reported as stale.
NARROW_ROOTS: dict[str, str] = {
    "test_duplicate_code.py": "globs under APP (backend/app)",
    "test_page_items_validation.py": "globs under APP (backend/app)",
}


def _skip_set(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [t.id for t in targets if isinstance(t, ast.Name)]
        if not names or not any(re.search(r"SKIP|EXCLUDE|IGNORE", name) for name in names):
            continue
        value = node.value
        if isinstance(value, (ast.Set, ast.Tuple, ast.List)):
            members = {
                elt.value for elt in value.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
            }
            if members:
                return members
    return set()


def _walks_repository_root(path: Path) -> bool:
    """True when the file globs from `REPO` itself rather than from a subdirectory of it."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"REPO\s*\.\s*rglob\(", text):
        return True
    # `Path(...).rglob` over a name that is assigned from REPO also counts.
    return bool(re.search(r"^\s*[A-Z_]+\s*=\s*REPO\s*$", text, re.MULTILINE) and re.search(r"\b[A-Z_]+\.rglob\(", text))


def test_the_scan_finds_the_skip_sets_and_the_walk_roots():
    files = sorted(TESTS.glob("*.py"))
    sets = {path.name: _skip_set(path) for path in files}
    sets = {name: members for name, members in sets.items() if members}
    assert len(sets) >= 5, f"only {len(sets)} skip sets were found, which is too few to be real"

    walkers = [path for path in files if _walks_repository_root(path)]
    assert walkers, "no file appears to walk the repository root, so the rule below would be vacuous"


def test_a_repository_wide_walk_skips_node_modules():
    offenders: list[str] = []
    for path in sorted(TESTS.glob("*.py")):
        if not _walks_repository_root(path):
            continue
        members = _skip_set(path)
        if HOSTILE_AT_ROOT not in members:
            offenders.append(f"{path.name}: walks the repository root with skip set {sorted(members)}")
    assert offenders == [], (
        f"these guards would read {HOSTILE_AT_ROOT}/, where this project's code does not live:\n  "
        + "\n  ".join(offenders)
    )


def test_the_documented_narrow_roots_still_are_narrow():
    """Both directions: a file recorded as narrow must still be narrow, or the record is hiding a change."""
    stale = sorted(name for name in NARROW_ROOTS if _walks_repository_root(TESTS / name))
    assert stale == [], (
        "these files are recorded as globbing under a narrow root but now walk the repository root, so their skip set "
        f"has to be widened in the same change: {stale}"
    )
    missing = sorted(name for name in NARROW_ROOTS if not (TESTS / name).is_file())
    assert missing == [], f"NARROW_ROOTS names files that no longer exist: {missing}"
