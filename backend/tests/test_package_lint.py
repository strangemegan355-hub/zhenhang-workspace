"""The packages have a lint config but no gate. Pin the reviewed problems and fail on anything new.

Round 92 found that `governance:check` runs `lint:web`, which lints `apps/web-admin` only. The root
`eslint.config.mjs` does cover `packages/*/src/**/*.{ts,tsx}` — its header says so, and that the packages "had no
lint coverage at all" before it — but **no script invokes it**, and it can only be run from the repository root:
invoking it through the app's workspace (whose cwd is `apps/web-admin`) makes eslint treat `packages` as outside
the base path and ignore it. So the coverage existed on paper only.

This runs it the way that works and pins the reviewed problems, the same shape as
`tests/test_scope_coverage.py` and `tests/test_layer_parity.py`: a new problem fails, and a stale entry fails
too. Nothing is silenced — the four errors are real and are decisions for someone with a browser, not something
to paper over with a disable comment.

The three warnings are React Compiler "Compilation Skipped: Use of incompatible library" notices about TanStack
Virtual. They are not actionable from this code: the library's `useVirtualizer()` returns functions that cannot
be memoized, which is the library's design.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
ESLINT = REPO / "apps" / "web-admin" / "node_modules" / ".bin" / "eslint.cmd"
ROOT_CONFIG = REPO / "eslint.config.mjs"

# Reviewed problems, keyed by (relative file, rule, line). Each is a decision rather than a defect:
#   data-grid:76   the effect reads localStorage and sets state once; the code notes that a lazy initializer
#                  would run during prerender and cause a hydration mismatch, so the effect is deliberate
#   data-grid:91   resetting column order when `columns` changes is the intended behaviour. The effect now returns
#                  the previous array when the keys are unchanged, so it no longer writes state on every render —
#                  `columns` arrives as an inline literal at thirty-three call sites — but the compiler diagnostic
#                  is about `setState` in an effect at all, so it stays until the component is restructured
#   data-grid:103  clearing the selection when `rows` changes is the intended behaviour
#   use-undo-redo:20  seeding the present value from `externalValue` on mount is how the hook starts — and both
#                     of these live in code nothing renders: `useUndoRedo`'s only consumer is `QuoteWorkbench`,
#                     which no page, app or package uses (round 121). Deleting the two files clears both.
# The last three warnings are library notices and are unavoidable here.
REVIEWED: set[tuple[str, str, int]] = {
    # Line numbers drift with DataGrid edits; same three deliberate setState-in-effect sites.
    ("packages/data-grid/src/index.tsx", "react-hooks/set-state-in-effect", 86),
    ("packages/data-grid/src/index.tsx", "react-hooks/set-state-in-effect", 101),
    ("packages/data-grid/src/index.tsx", "react-hooks/set-state-in-effect", 113),
    ("packages/quote-builder/src/bom-tree-editor.tsx", "react-hooks/incompatible-library", 89),
    ("packages/quote-builder/src/quote-line-editor.tsx", "react-hooks/incompatible-library", 26),
    ("packages/quote-builder/src/use-undo-redo.ts", "react-hooks/set-state-in-effect", 20),
    ("packages/quote-builder/src/use-undo-redo.ts", "react-hooks/exhaustive-deps", 24),
}


def _problems() -> set[tuple[str, str, int]]:
    if not ESLINT.exists():
        pytest.skip(f"eslint is not installed at {ESLINT.relative_to(REPO)}")
    # Run from the repository root: the config's own header explains why, and eslint resolves `files` patterns
    # relative to where it is invoked from.
    result = subprocess.run(
        [str(ESLINT), "packages", "--format", "json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        shell=False,
    )
    payload = result.stdout.strip()
    if not payload.startswith("["):
        pytest.fail(f"eslint produced no JSON report (exit {result.returncode}):\n{result.stderr[:800]}")
    found: set[tuple[str, str, int]] = set()
    for entry in json.loads(payload):
        relative = Path(entry["filePath"]).relative_to(REPO).as_posix()
        for message in entry["messages"]:
            if message.get("ruleId"):
                found.add((relative, message["ruleId"], int(message.get("line") or 0)))
    return found


def test_the_packages_have_no_unreviewed_lint_problems():
    found = _problems()
    new = sorted(found - REVIEWED)
    stale = sorted(REVIEWED - found)

    assert not new, (
        "these lint problems are not in the reviewed list. Fix them, or add them with the reason they stand:\n"
        + "\n".join(f"    {entry!r}," for entry in new)
    )
    assert not stale, (
        "these reviewed problems are gone, so the list is out of date. Remove them:\n"
        + "\n".join(f"    {entry!r}," for entry in stale)
    )
