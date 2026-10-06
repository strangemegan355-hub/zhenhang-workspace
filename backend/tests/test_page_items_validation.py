"""No page may be built by handing the queried list over unconverted.

`PageResponse.items` is a bare `list`, so a route with `response_model=PageResponse` validates nothing: whatever the
query returned is serialised as it came. The defect has one mechanically decidable shape — **`items=<bare name>`** —
and it caught every real instance: `workflow_service` (round 125), `notifications.py`, `equipment_units.py` and
`config_application_service.py` (round 126), `file_application_service.list_file_objects` and
`audit_service.list_audit_logs` (round 127).

The measured cost of missing it, from the notification page: `Notification` has **20 mapped columns** against **13**
in `NotificationRead`, so `provider_id`, `provider_type`, `config`, `creator`, `is_enabled`, `code` and `name` reached
the client, `config` being a provider's configuration. For the file page the same shape would have sent `creator` and
`relations` — the latter a relationship — and the four front-end files that use files read none of those fields, so
validating removed them without changing the contract.

**Two earlier drafts are the reason this one looks for a shape rather than for an omission.** One banned all
construction outside `app/schemas/` and compared `backend/app/...` paths against `app/schemas`; the next looked for a
missing `model_validate` and therefore reported `admin_service.list_roles` (`RoleRead.from_role`) and
`aftersales_service.list_requests` (`_to_read`), which both convert every row. A rule that cannot tell a converter
from a pass-through produces noise, and noise becomes an exception list. This rule needs exactly one reviewed entry.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
APP = BACKEND / "app"
SKIP_PARTS = {"__pycache__", ".venv"}
SCHEMA_PACKAGE = "schemas"

# Pass-through sites that were read and are correct. The reason has to be checkable in the code itself.
REVIEWED_PASS_THROUGH: dict[str, str] = {
    # `summaries: list[CustomerLedgerSummaryRead]` filled from `_summarize_customer`, so the items are already
    # schema instances and the annotation says so; there is nothing to validate.
    "services/ledger_service.py": "items are CustomerLedgerSummaryRead instances built by _summarize_customer",
}


def pass_through_sites() -> list[tuple[str, str, int, str]]:
    """(app-relative file, enclosing function, line, the name handed over) for `items=<bare name>`."""
    sites: list[tuple[str, str, int, str]] = []
    for path in sorted(APP.rglob("*.py")):
        if SKIP_PARTS & set(path.parts):
            continue
        relative = path.relative_to(APP).as_posix()
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or getattr(node.func, "id", None) != "PageResponse":
                continue
            for keyword in node.keywords:
                if keyword.arg != "items" or not isinstance(keyword.value, ast.Name):
                    continue
                owner = "<module>"
                for candidate in ast.walk(tree):
                    if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        end = getattr(candidate, "end_lineno", candidate.lineno)
                        if candidate.lineno <= node.lineno <= end:
                            owner = candidate.name
                sites.append((relative, owner, node.lineno, keyword.value.id))
    return sites


def test_the_scan_can_see_the_validating_helper():
    # Positive control: `page_response` validates, and the scan must be able to find its construction.
    total = sum(
        1
        for path in APP.rglob("*.py")
        if "PageResponse(" in path.read_text(encoding="utf-8", errors="replace")
    )
    assert total > 0, "no PageResponse construction was found anywhere, so this scan is broken"


def test_no_page_hands_the_queried_list_over_unconverted():
    found = pass_through_sites()
    new = sorted(site for site in found if site[0] not in REVIEWED_PASS_THROUGH)
    assert not new, (
        "these functions hand the queried list straight to `PageResponse(items=<name>)`. Because "
        "`PageResponse.items` is a bare `list` and route models are not generic, the rows reach the client exactly "
        "as the query returned them — round 126 measured that as seven internal columns of `Notification`, "
        "`config` among them. Convert each row with the read schema, call "
        "`page_response(total, page, page_size, items, Schema)`, or record the site in REVIEWED_PASS_THROUGH with a "
        "reason visible in the code:\n"
        + "\n".join(f"    {relative}:{line}  in {owner}  (items={name})" for relative, owner, line, name in new)
    )
    stale = [relative for relative in REVIEWED_PASS_THROUGH if relative not in {site[0] for site in found}]
    assert not stale, (
        "these reviewed pass-throughs no longer exist, so the record is out of date:\n"
        + "\n".join(f"    {relative}" for relative in stale)
    )
