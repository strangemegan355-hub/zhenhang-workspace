"""No backend module may read a scoped model while mentioning no scope marker at all.

Round 92's `test_scope_coverage.py` requires that **a module which applies a scope predicate somewhere applies it
everywhere** — so its rule cannot see a module that never scopes, which is exactly the shape round 196 found in the
copilot: the module applied a predicate in its caller, and its own two panels were unscoped.

Measured in round 199 over **309 backend files**: **19** select a model and mention no scope marker anywhere. They are
reviewed here with the reason each is correct, so a twentieth fails this test rather than arriving unnoticed.

**The reviewed set is a starting list, not a claim that these are safe** — every entry says *why*, and the four reasons
are genuinely different, which is the point: "no marker" is not one condition.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

# Every way a scope decision reaches a query here, including the self-scope by receiver that round 198 identified.
SCOPE_MARKERS = (
    "scope_predicate",
    "predicate",
    "owner_scope_user_id",
    "current_user",
    "user.id",
    "receiver_id",
    "assigned_to",
    "created_by ==",
    "data_scope",
)

# Reviewed in round 199. The reason is what makes an entry correct, so it is recorded per group rather than per file.
REVIEWED: dict[str, str] = {
    # 1. Repositories whose caller supplies `predicate=scope_predicate(...)`. They are the leaf that receives the
    #    decision, and rounds 85-90 established the pattern that the guard lives where the user is.
    "app/repositories/acceptance_repository.py": "receives the caller's predicate",
    "app/repositories/audit_repository.py": "receives the caller's predicate",
    "app/repositories/equipment_unit_repository.py": "receives the caller's predicate",
    "app/repositories/installation_plan_repository.py": "receives the caller's predicate",
    "app/repositories/machine_repository.py": "receives the caller's predicate",
    "app/repositories/option_group_repository.py": "receives the caller's predicate",
    "app/repositories/procurement_payable_repository.py": "receives the caller's predicate",
    "app/repositories/product_repository.py": "receives the caller's predicate",
    "app/repositories/quote_receivable_repository.py": "receives the caller's predicate",
    "app/repositories/workflow_repository.py": "receives the caller's predicate",
    # 2. The admin surfaces. Round 180 measured that Role, Permission, Department and User have no data-scope column at
    #    all, so these modules cannot receive a predicate for them.
    "app/repositories/admin_repository.py": "manages the four models that carry no data-scope column (round 180)",
    "app/repositories/user_repository.py": "same; users are the scope holders rather than scoped rows",
    # 3. Operational paths where a per-user scope would be wrong.
    "app/realtime/retention.py": "a retention purge, not a user-facing read",
    "app/realtime/store.py": "the replay store; the ACL is applied at the subscription point (realtime.py:262)",
    "app/services/mes_integration_service.py": "machine telemetry, no per-user owner",
    # 4. Post-authorisation lookups: the scoped read has already happened and returned 404 on failure.
    "app/services/machine_pricing_service.py": "the machine is 404-checked on the line above",
    "app/domains/quote/application/quote_export_payload.py": (
        "resolves the names of entities the quote already references; round 195 reviewed the pair"
    ),
    "app/domains/events/repositories/domain_event_repository.py": "domain events are a system log",
    "app/domains/events/repositories/task_queue_repository.py": "the task queue is a system queue",
}


def _files_selecting_without_markers() -> set[str]:
    import app.models  # noqa: F401 - registers the metadata
    from app.models import Base

    for module in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module(f"app.models.{module.name}")
    model_names = {mapper.class_.__name__ for mapper in Base.registry.mappers}

    found: set[str] = set()
    files = [p for p in (BACKEND / "app").rglob("*.py") if p.is_file() and "__pycache__" not in p.parts]
    for path in files:
        source = path.read_text(encoding="utf-8", errors="replace")
        if any(marker in source for marker in SCOPE_MARKERS):
            continue
        selects = False
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
                if name == "select" and any(
                    isinstance(a, ast.Name) and a.id in model_names for a in node.args
                ):
                    selects = True
                    break
        if selects:
            found.add(path.relative_to(BACKEND).as_posix())
    return found


def test_the_scan_finds_the_backend():
    files = [p for p in (BACKEND / "app").rglob("*.py") if p.is_file() and "__pycache__" not in p.parts]
    # The floor is the filesystem's, not a constant: a scan that found a handful would mean the walk broke.
    assert len(files) >= 250, f"only {len(files)} backend files were found, so the walk is broken"


def test_modules_that_never_scope_are_the_reviewed_set():
    found = _files_selecting_without_markers()
    added = sorted(found - set(REVIEWED))
    removed = sorted(set(REVIEWED) - found)
    assert not added and not removed, (
        "the set of modules that select a model without mentioning any scope marker changed.\n"
        f"  new:      {added or 'none'}\n"
        f"  now scoping or gone: {removed or 'none'}\n"
        "A new one is the round-196 shape: a module whose reads have no scope decision anywhere in it. If it is correct — "
        "a system queue, a purge, or a lookup whose scoped read already happened — add it here **with the reason**, "
        "because that reason is the thing this test is really recording."
    )
