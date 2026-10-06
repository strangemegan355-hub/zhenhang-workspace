"""Modules that apply a data-scope predicate must apply it to every row they read by id.

Rounds 85-90 fixed 18 call sites that read a row without the predicate while their own module applied one
elsewhere: the quote domain, the file domain, five modules' state transitions, the dashboard's profit aggregate,
two accounting posting references, two work-order project lookups and a procurement batch. Nothing stops the
next one being written, and neither the suites nor `ci.sh` would notice.

This is the same shape as `tests/test_layer_parity.py`: the reviewed exceptions are pinned explicitly, and
anything new fails. The entries are keyed by (file, enclosing function, called function) rather than by line
number, because a patch that changes line counts makes line numbers stale — round 90 learned that from a
traceback that pointed at the wrong line.

A stale entry fails too, so the list cannot rot into a list of things that no longer exist.
"""

from __future__ import annotations

import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

# Without the trailing parenthesis, so `scope_predicate_via_parent(` counts: matching the bare name
# is what keeps this from reporting a correctly scoped function as an exception.
SCOPING_HELPERS = ("scope_predicate", "owner_scope_user_id(", "build_created_by_filter(")
FUNC = re.compile(r"^(?:async )?def (\w+)\(")
CALL = re.compile(r"(?:await\s+)?(?:repo|self\.repo|(\w+_repo))\.((?:get|list|find|count|sum)_\w+)\(")

# Reviewed exceptions, each read in place during rounds 91-92. Grouped by the reason it is correct, so the next
# reader can check the reasoning rather than trusting the list.
REVIEWED: set[tuple[str, str, str]] = {
    # global or shared rows: scoping these would be wrong
    ("app/domains/config/application/config_application_service.py", "create_config", "get_config_by_key"),
    ("app/domains/quote/application/quote_application_service.py", "create_customer_quote", "get_generic_machine_id"),
    ("app/domains/quote/application/quote_application_service.py", "get_approval_template_detail", "get_approval_template"),
    ("app/domains/quote/application/quote_application_service.py", "get_approval_template_detail", "list_approval_nodes"),
    ("app/domains/quote/application/quote_application_service.py", "list_approval_templates", "list_approval_templates"),
    # a cache row, keyed by the object it caches
    ("app/domains/file/application/file_application_service.py", "cache_preview_url", "get_preview_cache"),
    # a row this same request has just created
    ("app/services/accounting_service.py", "create_entry", "get_entry"),
    ("app/services/accounting_service.py", "post_source_expense", "get_entry"),
    # a dedupe probe, on records that arrive from an already-scoped batch
    ("app/services/procurement_service.py", "_transfer_one_entry", "find_by_procurement_ref"),
    # derived reads of an already-scoped parent: these take the object, not an id
    ("app/domains/quote/application/quote_application_service.py", "current_approval_node", "list_approval_nodes"),
    ("app/domains/quote/application/quote_application_service.py", "resolve_next_approval_node", "list_approval_nodes"),
    ("app/services/project_service.py", "_build_project_profit_context", "find_linked_quote"),
    ("app/services/project_service.py", "_build_project_profit_context", "find_linked_cost_estimate"),
    ("app/services/project_service.py", "_build_project_profit_context", "find_current_quote_version"),
    ("app/services/project_service.py", "_build_project_profit_context", "count_quotes_for_project"),
    ("app/services/project_service.py", "_build_project_profit_context", "count_cost_estimates_for_project"),
    ("app/services/project_service.py", "_build_project_profit_context", "sum_amount_by_project"),
    # the guard deliberately lives at the route, which is where the user is (round 86)
    ("app/domains/quote/application/quote_application_service.py", "compare_quote_versions", "get_quote_version_by_no"),
    ("app/domains/quote/application/quote_application_service.py", "compare_quote_versions", "list_quote_items_by_version"),
    ("app/domains/quote/application/quote_application_service.py", "get_export_task", "get_export_task"),
}


def _unscoped_calls() -> set[tuple[str, str, str]]:
    found: set[tuple[str, str, str]] = set()
    for path in sorted((BACKEND / "app").rglob("*.py")):
        if "/repositories/" in path.as_posix() or path.name == "data_scope.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(helper in text for helper in SCOPING_HELPERS):
            continue
        lines = text.splitlines()
        starts = [(i, FUNC.match(line).group(1)) for i, line in enumerate(lines) if FUNC.match(line)]
        starts.append((len(lines), "<module>"))
        relative = path.relative_to(BACKEND).as_posix()
        for index in range(len(starts) - 1):
            begin, name = starts[index]
            body = "\n".join(lines[begin : starts[index + 1][0]])
            if any(helper in body for helper in SCOPING_HELPERS):
                continue  # the function scopes something itself
            for match in CALL.finditer(body):
                call_line = body[: match.start()].count("\n") + begin
                window = "\n".join(lines[call_line : call_line + 6])
                if "predicate=" in window or "created_by=" in window or "owner_id" in window:
                    continue
                found.add((relative, name, match.group(2)))
    return found


def test_no_module_reads_a_scoped_row_without_the_predicate():
    found = _unscoped_calls()
    newly_unscoped = sorted(found - REVIEWED)
    stale = sorted(REVIEWED - found)

    assert not newly_unscoped, (
        "these reads have no data-scope predicate although their module applies one elsewhere.\n"
        "Either pass `predicate=scope_predicate(Model, current_user)` (see rounds 85-90 for the pattern), or add\n"
        "the entry to REVIEWED with the reason it is correct:\n"
        + "\n".join(f"    {entry!r}," for entry in newly_unscoped)
    )
    assert not stale, (
        "these REVIEWED entries no longer exist, so the list is describing code that has moved or been fixed.\n"
        "Remove them (the guard against regression is the entry itself):\n"
        + "\n".join(f"    {entry!r}," for entry in stale)
    )
