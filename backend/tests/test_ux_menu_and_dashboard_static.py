"""UX-001/002/006 static acceptance pins (no DB, no app import).

UX-001: machines/BOM path hidden from sidebar; products remain visible.
UX-002: customer quotes sidebar entry hidden; quotes center remains.
UX-006: dashboard keeps action-first cards; permission gates on finance/approval cards;
         WorkflowProgress / RecentFiles not mounted on the page.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MENU = REPO / "apps" / "web-admin" / "src" / "lib" / "menu.ts"
DASHBOARD = REPO / "apps" / "web-admin" / "src" / "app" / "(admin)" / "dashboard" / "page.tsx"
FINANCE_CARD = REPO / "apps" / "web-admin" / "src" / "components" / "dashboard" / "FinanceActionCard.tsx"
APPROVAL_CARD = REPO / "apps" / "web-admin" / "src" / "components" / "dashboard" / "ApprovalCenterCard.tsx"
WORK_ORDERS_CARD = (
    REPO / "apps" / "web-admin" / "src" / "components" / "dashboard" / "RecentWorkOrdersCard.tsx"
)


def _text(path: Path) -> str:
    assert path.is_file(), f"missing {path}"
    return path.read_text(encoding="utf-8")


def test_ux001_machines_path_hidden_products_visible():
    menu = _text(MENU)
    assert 'href: "/products"' in menu
    assert 'href: "/machines"' in menu
    assert 'href: "/machines", permission: "master:machine:read", hidden: true' in menu
    assert 'href: "/boms", permission: "master:bom:read", hidden: true' in menu
    # Products entry must not be marked hidden on the same line pattern as machines.
    assert 'href: "/products", permission: "master:product:read", hidden: true' not in menu


def test_ux002_customer_quotes_sidebar_hidden():
    menu = _text(MENU)
    assert 'href: "/quotes", permission: "business:quote:read"' in menu
    assert (
        'href: "/quotes/customer", permission: "business:quote:read", hidden: true' in menu
    )


def test_ux006_dashboard_action_first_and_no_legacy_cards():
    page = _text(DASHBOARD)
    assert "ApprovalCenterCard" in page
    assert "NotificationCenterCard" in page
    assert "FinanceActionCard" in page
    assert "WorkflowProgressCard" not in page
    assert "RecentFilesCard" not in page
    assert "UX-006" in page


def test_ux006_finance_and_approval_cards_permission_gated():
    finance = _text(FINANCE_CARD)
    approval = _text(APPROVAL_CARD)
    work = _text(WORK_ORDERS_CARD)
    assert "business:accounting:read" in finance
    assert "hasPermission" in finance
    assert "return null" in finance
    assert "business:approval:read" in approval
    assert "hasPermission" in approval
    assert "return null" in approval
    assert "business:work_order:read" in work
    assert "hasPermission" in work
    assert "return null" in work


def _role_perm_codes(seed_src: str, role_code: str) -> set[str]:
    """Extract permission codes for one TRIAL_ROLE_DEFS entry (static parse, no import)."""
    marker = f'(\n        "{role_code}",'
    start = seed_src.find(marker)
    assert start >= 0, f"role {role_code} missing in setup_trial_users"
    # Next role block or end of TRIAL_ROLE_DEFS.
    nxt = seed_src.find("\n    (\n        \"", start + len(marker))
    if nxt < 0:
        nxt = seed_src.find("\n]\n\n# username", start)
    chunk = seed_src[start : nxt if nxt > start else start + 12000]
    # Skip the role_code tuple itself; keep ("perm:code", "中文名", ...)
    return set(re.findall(r'\("([a-z][a-z0-9_:.]+)",\s*"', chunk)) - {role_code}


def test_ux006_seed_roles_card_visibility_matrix():
    """K-006: seed role perms imply which Dashboard gated cards should show.

    Cards: 财务待办←accounting:read · 审批中心←approval:read · 最近工单←work_order:read
    """
    seed = _text(REPO / "backend" / "scripts" / "setup_trial_users.py")
    expected = {
        # trialadmin = user trialadmin / role trial_admin
        "trial_admin": {"finance": False, "approval": False, "work_orders": False},
        "trial_finance": {"finance": True, "approval": True, "work_orders": True},
        "trial_sales": {"finance": True, "approval": False, "work_orders": True},
        "workshop": {"finance": False, "approval": False, "work_orders": True},
    }
    for role_code, cards in expected.items():
        perms = _role_perm_codes(seed, role_code)
        got = {
            "finance": "business:accounting:read" in perms,
            "approval": "business:approval:read" in perms,
            "work_orders": "business:work_order:read" in perms,
        }
        assert got == cards, f"{role_code}: {got} != {cards}"
