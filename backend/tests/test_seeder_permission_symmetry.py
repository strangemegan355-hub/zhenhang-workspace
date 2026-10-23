"""Trial seeder permission policy — exact sync (product decision recorded 2026-10-23).

Earlier rounds recorded an asymmetry: the seeder only appended, while `admin_service`
could replace a role's full permission list. That left forbidden codes
(`platform:config:*`) on already-seeded trial roles forever, and left required codes
(`business:workshop:read`, accounting) missing until someone noticed.

**Product decision (K-016):** for *trial* roles defined in `TRIAL_ROLE_DEFS`, the seeder
**is** the source of truth. Re-running `setup_trial_users.py` reconciles each trial role
to the declared set (add missing, drop extras). Manual admin grants on those roles are
intentionally overwritten on the next seed — trial accounts are disposable pilot identities,
not production RBAC edited in Desk.

Custom / non-trial roles remain editable via the admin API (`set_role_permissions`).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

SEEDER = BACKEND / "scripts" / "setup_trial_users.py"
ADMIN_SERVICE = BACKEND / "app" / "services" / "admin_service.py"


def _role_permission_assignment(path: Path) -> str:
    """Every textual form in which the file attaches or replaces a role's permissions."""
    source = path.read_text(encoding="utf-8", errors="replace")
    findings: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"append", "extend", "remove", "clear"}:
                target = node.func.value
                name = getattr(target, "attr", "")
                if "permission" in name:
                    findings.append(f"line {node.lineno}: .{node.func.attr}()")
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and "permission" in target.attr:
                    findings.append(f"line {node.lineno}: assignment to .{target.attr}")
    return "\n".join(findings)


def test_the_trial_seeder_reconciles_role_permissions_to_the_definition():
    """Pinned: trial roles are exact-synced, not append-only."""
    mechanism = _role_permission_assignment(SEEDER)
    assert "assignment to .permissions" in mechanism, (
        "expected the trial seeder to replace `.permissions` with the declared set "
        "(K-016 exact sync). Mechanism found:\n" + mechanism
    )


def test_the_admin_api_can_still_replace_a_roles_permissions():
    """Admin plane remains able to replace arbitrary roles; trial seed does not remove that path."""
    admin = _role_permission_assignment(ADMIN_SERVICE)
    assert "assignment to .permissions" in admin, (
        "`admin_service` no longer replaces a role's permission list — update this guard "
        "if the admin API shape changed:\n" + admin
    )
