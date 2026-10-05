"""A route's permission code must name the capability it guards.

Function-level authorization only means something when the code says what it protects. Three MES
endpoints and the workshop board were guarded by `business:quote:*`: any role that could edit a
quote could post machine telemetry, and withdrawing quote access would have silently broken the
shop floor.

The last test asserts the cross-layer agreement the eight-layer rule asks for — the code the API
requires is the code the web-admin menu gates the page with.

Nothing here imports the application, so the module needs no environment and cannot fail at
collection.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
ENDPOINTS = BACKEND / "app" / "api" / "v1" / "endpoints"
SEED = BACKEND / "scripts" / "setup_trial_users.py"
MENU = REPO / "apps" / "web-admin" / "src" / "lib" / "menu.ts"

REQUIRE = re.compile(r'require_permissions\("([^"]+)"\)')

MES_CODES = ("business:mes:read", "business:mes:write")
WORKSHOP_CODE = "business:workshop:read"


def required_codes(module: str) -> set[str]:
    return set(REQUIRE.findall((ENDPOINTS / module).read_text(encoding="utf-8")))


def seeded_codes() -> dict[str, set[str]]:
    """role code -> permission codes, read structurally so a rename cannot fool the test."""
    tree = ast.parse(SEED.read_text(encoding="utf-8"))
    roles: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "TRIAL_ROLE_DEFS":
                value = node.value
        elif isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "TRIAL_ROLE_DEFS" in names:
                value = node.value
        if value is None:
            continue
        for element in value.elts:
            role_code = element.elts[0].value
            permissions = {permission.elts[0].value for permission in element.elts[3].elts}
            roles[role_code] = permissions
    return roles


def test_mes_endpoints_use_mes_codes():
    codes = required_codes("mes.py")
    for code in MES_CODES:
        assert code in codes, f"mes.py no longer requires {code}"
    borrowed = sorted(code for code in codes if code.startswith("business:quote:"))
    assert borrowed == [], f"mes.py guards MES with quote codes: {borrowed}"


def test_workshop_board_uses_its_own_code():
    codes = required_codes("workshop.py")
    assert codes == {WORKSHOP_CODE}, codes


def test_the_new_codes_are_granted_to_a_role():
    roles = seeded_codes()
    assert roles, "TRIAL_ROLE_DEFS could not be read"
    granted = set().union(*roles.values())
    for code in (*MES_CODES, WORKSHOP_CODE):
        assert code in granted, f"{code} is required by a route but no provisioned role holds it"
    # The shop floor is the role that operates the board and reads machine signals.
    assert WORKSHOP_CODE in roles["workshop"]
    assert "business:mes:read" in roles["workshop"]


def test_menu_gate_matches_the_api_guard():
    if not MENU.exists():
        return
    match = re.search(r'href: "/workshop", permission: "([^"]+)"', MENU.read_text(encoding="utf-8"))
    assert match, "the /workshop menu entry lost its permission gate"
    assert match.group(1) in required_codes("workshop.py")
