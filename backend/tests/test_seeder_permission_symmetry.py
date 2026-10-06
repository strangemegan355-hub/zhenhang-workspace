"""The trial seeder can grant a permission and cannot take one back — recorded, with the question that decides it.

Round 218 looked at the one item on the decision list that might have been engineering symmetry rather than a product
choice: *may `setup_trial_users.py` remove permissions?* The measurement sharpens it:

* `setup_trial_users.py:406-411` builds `existing_ids` from the role's current permissions and then **appends** — **the
  script only ever adds**;
* a repository-wide search for revocation finds nothing but the association table's own definition — **nothing in the
  project can take a permission away from a role except `admin_service.set_role_permissions`, which replaces the whole
  list** (`role.permissions = permissions`).

So a code deleted from `TRIAL_ROLE_DEFS` **stays granted forever on an already-seeded database**, and the re-run that
`README.md` and `ci.yml` perform on every start will never remove it.

**This is not purely engineering symmetry, and the reason is a single product question:** *is the seeder the only source
of a trial role's permissions?* On a freshly seeded database it is, and reconciling to the definition would be correct. If
an administrator has ever granted one of those roles an extra code through the admin API, **reconciling would silently
revoke that administrator's decision**. **Both policies are defensible and they contradict, so the choice is the user's —
and this test records the asymmetry and the question rather than picking one.**

What *is* pinned here is the mechanism, so that a change to either side is a visible decision.
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


def test_the_seeder_only_ever_appends_role_permissions():
    """Pinned so that giving the seeder a revocation path is a deliberate change with a reason.

    **The reason has to say which policy was chosen** — reconcile the definition (correct if the seeder is the only
    source, destructive if an administrator has edited the role) or keep appending and report the drift instead.
    """
    mechanism = _role_permission_assignment(SEEDER)
    assert ".append()" in mechanism, (
        "the trial seeder no longer appends role permissions, so this guard cannot describe what it does:\n" + mechanism
    )
    assert ".remove()" not in mechanism and ".clear()" not in mechanism, (
        "the trial seeder now **revokes** role permissions. That is the change this record was waiting for — **make sure "
        "the policy was chosen deliberately**, because on a database where an administrator has granted one of these "
        "roles an extra code through the admin API, revoking silently undoes that decision:\n" + mechanism
    )


def test_the_admin_api_can_replace_a_roles_permissions_and_the_seeder_cannot():
    """The asymmetry, stated as a test so that a reader meets it rather than discovering it."""
    admin = _role_permission_assignment(ADMIN_SERVICE)
    assert "assignment to .permissions" in admin, (
        "`admin_service` no longer replaces a role's permission list, so the asymmetry this test describes has changed "
        "shape — read the new form and update both this test and the note above:\n" + admin
    )
    seeder = _role_permission_assignment(SEEDER)
    assert "assignment to .permissions" not in seeder, (
        "the seeder now replaces the permission list. **If that was deliberate, the product question in this file's "
        "docstring has been answered — record the answer here**:\n" + seeder
    )
