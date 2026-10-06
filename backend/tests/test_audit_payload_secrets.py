"""Two promises about credentials, and the structures that already keep them.

Round 212 collected every `never / always / only / must not` claim in `app/` — **15 modules, 24 claims** — and read the
three sharpest, all of which say *a secret or a privilege must not flow somewhere*:

* `app/schemas/user.py:66` — *"hashed_password must never be serialisable"* — **already guarded** by
  `test_admin_plane.py:313` (`assert "hashed_password" not in dumped`);
* `app/services/admin_service.py:89` — *"is_system is never client-controlled"* — **no test**;
* `app/services/admin_service.py:388` — *"The password never reaches the audit payload"* — **no test**.

Reading both, **each is already true, and true by construction rather than by care**:

* `RoleCreate` is `['code', 'data_scope', 'description', 'name']` and `RoleUpdate` is
  `['data_scope', 'description', 'name']` — **`is_system` cannot be set because no field carries it**;
* every `_audit` payload is either a literal dict or `changed`, and **each `changed` is built from its own explicit field
  tuple** — `update_user`'s is `("email", "full_name", "phone", "is_active")` — so a password has no path into it.

**That is the strongest form of the claim, and it is exactly what a test should pin**, because the structure is what makes
it drift-proof: adding a field to either list is a deliberate act that this test turns into a decision.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

ADMIN_SERVICE = BACKEND / "app" / "services" / "admin_service.py"

# The fields `update_user` is allowed to report to the audit log. Named here so that extending it is a visible change.
AUDITED_USER_FIELDS = ("email", "full_name", "phone", "is_active")
# And the keys `create_user` reports. Neither list may gain a credential-shaped name.
AUDITED_CREATE_USER_KEYS = {"username", "role_codes"}


def _function(name: str) -> ast.AsyncFunctionDef:
    tree = ast.parse(ADMIN_SERVICE.read_text(encoding="utf-8", errors="replace"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not in {ADMIN_SERVICE.name}; this guard has lost its subject")


def test_no_admin_write_schema_exposes_is_system():
    """`is_system is never client-controlled` — held because the field does not exist on the write schemas."""
    from app.schemas import admin as admin_schemas

    offenders: list[str] = []
    for name in ("RoleCreate", "RoleUpdate"):
        model = getattr(admin_schemas, name, None)
        assert model is not None, f"{name} is gone, so this guard cannot check it"
        if "is_system" in model.model_fields:
            offenders.append(f"{name} exposes is_system")

    assert offenders == [], (
        "these admin write schemas now accept `is_system`, so a client could mark its own role as a system role — the "
        "privilege `admin_service.py:89` promises is never client-controlled:\n  " + "\n  ".join(offenders)
    )


def test_the_audited_user_fields_are_the_recorded_ones():
    function = _function("update_user")
    tuples = [
        tuple(elt.value for elt in node.iter.elts if isinstance(elt, ast.Constant))
        for node in ast.walk(function)
        if isinstance(node, ast.For)
        and isinstance(node.iter, (ast.Tuple, ast.List))
        and all(isinstance(elt, ast.Constant) for elt in node.iter.elts)
    ]
    assert tuples, "update_user no longer iterates a literal field tuple, so this guard cannot reason about the audit"

    assert AUDITED_USER_FIELDS in tuples, (
        f"update_user's audited fields are now {tuples}, not {AUDITED_USER_FIELDS!r}. **The password must not reach the "
        "audit payload** — if this list grew deliberately, check that no new field is a credential, then update this "
        "test in the same change"
    )
    for fields in tuples:
        assert not any("password" in str(field) for field in fields), (
            f"update_user now audits {fields}, which names a password"
        )


def test_the_create_user_audit_payload_names_no_credential():
    function = _function("create_user")
    payloads = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "_audit"
    ]
    assert payloads, "create_user no longer calls _audit, so the password claim has no subject"

    keys: set[str] = set()
    for call in payloads:
        for keyword in call.keywords:
            if keyword.arg == "payload" and isinstance(keyword.value, ast.Dict):
                keys |= {
                    key.value
                    for key in keyword.value.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                }
    assert keys == AUDITED_CREATE_USER_KEYS, (
        f"create_user's audit payload keys are now {sorted(keys)}, not {sorted(AUDITED_CREATE_USER_KEYS)}. **The password "
        "never reaches the audit payload** — if a key was added deliberately, confirm it names no credential and update "
        "this test"
    )
