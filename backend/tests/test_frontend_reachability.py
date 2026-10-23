"""Front-end symbols that nothing references, measured beyond the documents that name them.

Round 121 found `QuoteWorkbench` exported and rendered nowhere, and `test_documentation_claims.py` made that standing —
**but only for names the documentation mentions**, a scope round 170 recorded deliberately. **A component no document
names was therefore outside every guard**, which is the "mock page" the objective asks to eliminate.

Round 186 walked `apps/*/src` and `packages/*/src` for exported PascalCase symbols and asked which are referenced
anywhere else. The first version called all 19 of them "unused" and **that label was wrong** — it measures "not referenced
from another file", and a symbol can be a package barrel export for a consumer that does not exist yet, or referenced
inside its own file. Splitting the 19 by that distinction is what makes the result actionable:

* **9 barrel exports with no consumer yet** — `AIChat`, `AIContextInjection`, `AIPanel` and `RetrievalPreview` from
  `ai-ui`, `AuthApi` from `api-sdk`, `QuoteBuilderShell`, `SchemaFormEngine`, `WorkflowGraph`, `WorkflowSchemaView`. This
  is the `QuoteWorkbench` class: exported for a consumer nobody wrote.
* **3 referenced NOWHERE at all**, not even inside their own file — `BOM_IMPORT_TEMPLATE`, `MasterRowActions`,
  `TableToolbar`.
* **7 referenced inside their own file**, so not unused at all — the label the first version would have put on them.

**Everything here is recorded, not deleted.** Removing an export is the user's decision, and the pending deletion
proposal covers the ones already agreed; this test's job is to keep the measurement current and to fail when a new
zero-reference symbol appears unremarked.
"""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKIP = {"node_modules", ".git", ".next", "dist", ".venv", "__pycache__", "build", "site-packages"}
EXPORTED = re.compile(r"^export (?:async )?(?:function|const|class) ([A-Z][A-Za-z0-9_]*)", re.MULTILINE)

# Measured in round 186. A symbol that becomes referenced, or a new one that is not, fails this test in one of its two
# directions; either way the record has to be updated in the same change.
BARREL_EXPORTS_WITHOUT_A_CONSUMER = {
    "AIChat",
    "AIContextInjection",
    "AIPanel",
    "AuthApi",
    "QuoteBuilderShell",
    "RetrievalPreview",
    "SchemaFormEngine",
    "WorkflowGraph",
    "WorkflowSchemaView",
}

REFERENCED_NOWHERE = {
    "BOM_IMPORT_TEMPLATE",
    "MasterRowActions",
    # UX-006 (2026-10-23): dashboard dropped these from the action-first layout;
    # files remain until a deliberate deletion pass.
    "RecentFilesCard",
    "TableToolbar",
    "WorkflowProgressCard",
}

# --- The hook layer, added in round 190. -------------------------------------------------------------------------------
# **Round 186's instrument required a capital first letter** — the React component convention — so **every `useXxx` hook
# was invisible to it.** Walking the same directories for hooks finds **203 exported hooks**, of which **13 are referenced
# by no other file and, unlike the three above, none of them is even used inside its own file.** They cluster:
#
# * `admin.ts` — `useUpdateDepartmentMutation`, `useUpdateRoleMutation`, `useUpdateUserMutation`: **the three admin edit
#   hooks whose wiring was an open question; they exist and no page calls them.**
# * `accounting.ts` — `useApproveQuoteReceivableMutation`, `useRejectQuoteReceivableMutation`,
#   `useCreateAccountingEntryMutation`, `useQuoteReceivableRequestsQuery`: **a whole quote-receivable approval flow.**
# * single detail queries in `aftersales`, `boms`, `equipment-units`, `machines`, `quotes`, and `useNotificationRealtime`
#   in `packages/realtime`.
#
# Recorded, not deleted: wiring them is a product decision, and removing them is the user's.
HOOKS_REFERENCED_NOWHERE = {
    "useAftersalesDetailQuery",
    "useApproveQuoteReceivableMutation",
    "useBomQuery",
    "useCreateAccountingEntryMutation",
    "useEquipmentUnitDetailQuery",
    "useMachinePricingProfileQuery",
    "useNotificationRealtime",
    "useQuoteDiffQuery",
    "useQuoteReceivableRequestsQuery",
    "useRejectQuoteReceivableMutation",
    "useUpdateDepartmentMutation",
    "useUpdateRoleMutation",
    "useUpdateUserMutation",
}

HOOK = re.compile(r"^export (?:async )?(?:function|const) (use[A-Z][A-Za-z0-9_]*)", re.MULTILINE)


def _sources() -> list[Path]:
    roots = [*(REPO / "apps").glob("*/src"), *(REPO / "packages").glob("*/src")]
    return sorted(
        p
        for root in roots
        if root.is_dir()
        for p in root.rglob("*")
        if p.is_file() and p.suffix in {".ts", ".tsx"} and not any(part in SKIP for part in p.relative_to(REPO).parts)
    )


def _measure() -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    sources = _sources()
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in sources}
    exports: dict[str, list[Path]] = defaultdict(list)
    for path, text in texts.items():
        for name in EXPORTED.findall(text):
            exports[name].append(path)

    barrels: dict[str, list[Path]] = defaultdict(list)
    nowhere: dict[str, list[Path]] = defaultdict(list)
    for name, definers in exports.items():
        use = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
        if any(use.search(text) for path, text in texts.items() if path not in definers):
            continue
        for definer in definers:
            occurrences = len(use.findall(texts[definer]))
            if occurrences > 1:
                continue  # referenced inside its own file
            (barrels if definer.name.startswith("index.") else nowhere)[name].append(definer)
    return barrels, nowhere


def test_the_scan_finds_the_front_end():
    sources = _sources()
    # The floor is the filesystem's: two apps and the packages must be present, and this is not a one-file scan.
    assert len(sources) >= 100, f"only {len(sources)} front-end source files were found"
    assert (REPO / "apps" / "web-admin" / "src").is_dir(), "apps/web-admin/src is missing from the walk"


def test_barrel_exports_without_a_consumer_are_the_recorded_set():
    barrels, _ = _measure()
    found = set(barrels)
    added = sorted(found - BARREL_EXPORTS_WITHOUT_A_CONSUMER)
    removed = sorted(BARREL_EXPORTS_WITHOUT_A_CONSUMER - found)
    assert not added and not removed, (
        "the set of package-barrel exports nothing consumes changed.\n"
        f"  new:      {added or 'none'}\n"
        f"  consumed: {removed or 'none'}\n"
        "A new one is the QuoteWorkbench class round 121 found; a consumed one means the record is stale."
    )


def test_symbols_referenced_nowhere_are_the_recorded_set():
    _, nowhere = _measure()
    found = set(nowhere)
    added = sorted(found - REFERENCED_NOWHERE)
    removed = sorted(REFERENCED_NOWHERE - found)
    assert not added and not removed, (
        "the set of front-end symbols referenced nowhere at all changed.\n"
        f"  new:      {added or 'none'}\n"
        f"  now used: {removed or 'none'}\n"
        "These are declared and used by nothing, not even in their own file. Removing them is the user's decision, "
        "recorded in the pending deletion proposal; this record has to move with them."
    )


def _hooks_referenced_nowhere() -> set[str]:
    """Exported `useXxx` hooks no other file references — the layer round 186's capital-letter regex could not see."""
    sources = _sources()
    texts = {p: p.read_text(encoding="utf-8", errors="replace") for p in sources}
    exports: dict[str, list[Path]] = defaultdict(list)
    for path, text in texts.items():
        for name in HOOK.findall(text):
            exports[name].append(path)

    found: set[str] = set()
    for name, definers in exports.items():
        use = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
        if any(use.search(text) for path, text in texts.items() if path not in definers):
            continue
        found.add(name)
    return found


def test_the_hook_layer_was_actually_scanned():
    sources = _sources()
    hooks = {name for path in sources for name in HOOK.findall(path.read_text(encoding="utf-8", errors="replace"))}
    # A floor from the filesystem rather than a constant: the hook layer is large, and a scan that found a handful would
    # mean the pattern stopped matching rather than that the hooks went away.
    assert len(hooks) >= 150, f"only {len(hooks)} exported hooks were found, so the hook scan is broken"


def test_hooks_referenced_nowhere_are_the_recorded_set():
    found = _hooks_referenced_nowhere()
    added = sorted(found - HOOKS_REFERENCED_NOWHERE)
    removed = sorted(HOOKS_REFERENCED_NOWHERE - found)
    assert not added and not removed, (
        "the set of exported hooks nothing consumes changed.\n"
        f"  new:      {added or 'none'}\n"
        f"  now used: {removed or 'none'}\n"
        "A new one is a hook written but never wired (the `admin.ts` trio and the quote-receivable flow were both this); "
        "a removed one means a page now calls it, which is the wiring the phase-4 alignment is waiting on."
    )
