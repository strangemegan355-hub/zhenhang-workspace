"""Repository reads of a scoped model that their caller cannot restrict.

A repository function without a `predicate` parameter gives its caller no way to narrow the rows, so a service
using one for a user-facing read is unscoped whatever it does. Round 113 found two that were exactly that — the
supplier ledger's summaries and the workshop board's kanban — and round 114 closed the same shape in the customer
ledger. Neither could be caught before, because `test_scope_coverage` looks for calls that **omit** `predicate=`,
and a function with no such parameter cannot be caught omitting it.

Every entry below was read and is legitimate:

* **document-number generators** must count every row, or two departments generate the same number;
* **idempotency lookups** must see every row to notice a duplicate;
* **reads through an already-scoped parent** take the parent object, not an id, so the caller has already been
  checked.

The list is asserted for equality in both directions: a new parameterless read fails here, and so does an entry
that no longer exists.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPOSITORIES = BACKEND / "app" / "repositories"
sys.path.insert(0, str(BACKEND / "tests"))
from test_data_scope_coverage import SCOPED_DOCUMENTS  # noqa: E402

# Controls: the detector must separate a function that takes a predicate from one that does not.
CONTROL_PARAMETERLESS = "count_entry_no_prefix"
CONTROL_TAKES_A_PREDICATE = "get_entry"

# Read one by one in rounds 113 and 114. Grouped in the module docstring by why each is correct.
REVIEWED_PARAMETERLESS_READS: set[tuple[str, str, str]] = {
    ("app/repositories/accounting_repository.py", "count_entry_no_prefix", "AccountingEntry"),
    ("app/repositories/accounting_repository.py", "get_entry_by_quote_source", "AccountingEntry"),
    ("app/repositories/accounting_repository.py", "get_entry_by_source", "AccountingEntry"),
    ("app/repositories/aftersales_repository.py", "generate_request_no", "AfterSalesServiceRequest"),
    ("app/repositories/cost_estimate_repository.py", "count_estimate_no_prefix", "CostEstimate"),
    ("app/repositories/fieldwork_repository.py", "count_record_no_prefix", "FieldworkRecord"),
    ("app/repositories/procurement_repository.py", "count_request_no_prefix", "ProcurementEntry"),
    ("app/repositories/project_actual_cost_repository.py", "find_by_procurement_ref", "ProjectActualCost"),
    ("app/repositories/project_actual_cost_repository.py", "sum_amount_by_project", "ProjectActualCost"),
    ("app/repositories/project_repository.py", "count_cost_estimates_for_project", "CostEstimate"),
    ("app/repositories/project_repository.py", "count_project_no_prefix", "Project"),
    ("app/repositories/project_repository.py", "count_quotes_for_project", "Quote"),
    ("app/repositories/project_repository.py", "find_linked_cost_estimate", "CostEstimate"),
    ("app/repositories/project_repository.py", "find_linked_quote", "Quote"),
    ("app/repositories/work_order_repository.py", "count_work_order_no_prefix", "WorkOrder"),
}


def parameterless_reads() -> set[tuple[str, str, str]]:
    """(file, function, model) for every repository read of a scoped model with no `predicate` parameter."""
    scoped_models = set(SCOPED_DOCUMENTS.values())
    found: set[tuple[str, str, str]] = set()
    for path in sorted(REPOSITORIES.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            arguments = {argument.arg for argument in node.args.args + node.args.kwonlyargs}
            if "predicate" in arguments:
                continue
            body = ast.get_source_segment(source, node) or ""
            for model in sorted(scoped_models):
                if re.search(rf"select(_from)?\(\s*{model}\b", body):
                    found.add((path.relative_to(BACKEND).as_posix(), node.name, model))
    return found


def test_the_detector_separates_the_two_known_cases():
    found = parameterless_reads()
    assert any(function == CONTROL_PARAMETERLESS for _file, function, _model in found), (
        f"{CONTROL_PARAMETERLESS} takes no predicate and must be found, so the detector is broken"
    )
    assert not any(function == CONTROL_TAKES_A_PREDICATE for _file, function, _model in found), (
        f"{CONTROL_TAKES_A_PREDICATE} takes a predicate and must not be listed, so the detector is broken"
    )


def test_every_parameterless_read_is_reviewed():
    found = parameterless_reads()

    # The difference first, the floor second. A stale record *grows* the reviewed list, so a floor of
    # `len(found) >= len(REVIEWED)` checked first would report a stale entry as "the detector is broken" — a
    # failure for the wrong reason, which the round 115 control run demonstrated.
    new = sorted(found - REVIEWED_PARAMETERLESS_READS)
    stale = sorted(REVIEWED_PARAMETERLESS_READS - found)
    assert not new, (
        "these repository functions read a scoped model but take no `predicate`, so their callers cannot restrict "
        "them. Add `predicate=None` and apply it, or record the entry with the reason it is correct:\n"
        + "\n".join(f"    {entry!r}," for entry in new)
    )
    assert not stale, (
        "these recorded functions no longer read a scoped model without a predicate, so the record is out of "
        "date:\n" + "\n".join(f"    {entry!r}," for entry in stale)
    )

    # No separate vacuity floor: **the stale assertion already is one.** A detector that silently found nothing
    # makes every recorded entry stale, so it fails here by name rather than passing. The round 115 control run
    # demonstrated the trade: checking a `len(found) >= len(REVIEWED)` floor first made a *stale* record report
    # "the detector is probably broken", which is a failure for the wrong reason, and the reordered version leaves
    # the floor unreachable. Two difference assertions cover both directions; a third would only add a wrong
    # message.
