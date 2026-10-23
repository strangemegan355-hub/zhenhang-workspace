"""
Verify trial role permission boundaries (offline, DB-based).

  python scripts/verify_permissions.py

Requires setup_trial_users.py to have been run.
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import selectinload, sessionmaker

from _script_utils import BACKEND_ROOT, database_url, print_db_target  # noqa: F401
from app.core.rbac import collect_permission_codes
from app.models.role import Role
from app.models.user import User

FORBIDDEN_FOR_TRIAL = frozenset(
    {
        # The admin plane administers accounts, roles and permissions. A trial account holding
        # any of these could widen its own authority in one step, so only the bootstrap
        # superuser has them. Department and tenant READS are delegated to trial_admin and are
        # deliberately absent from this set.
        "system:user:read",
        "system:user:create",
        "system:user:update",
        "system:user:assign",
        "system:role:read",
        "system:role:create",
        "system:role:update",
        "system:role:assign",
        "system:permission:read",
        "system:tenant:create",
        "system:tenant:update",
        "system:department:create",
        "system:department:update",
        "platform:config:read",
        "platform:config:create",
        "platform:config:update",
        "platform:audit:read",
        "platform:event:process",
        "platform:event:replay",
    }
)

ROLE_EXPECTATIONS: dict[str, dict[str, object]] = {
    "sales01": {
        "must_have": {
            "business:quote:read",
            "business:quote:create",
            "master:customer:read",
            "platform:notification:read",
        },
        "must_not_have": {
            "business:quote:approve",
            "master:bom:create",
            "master:bom_item:create",
            "platform:config:read",
            "system:user:read",
        },
    },
    "tech01": {
        "must_have": {
            "master:bom:read",
            "master:bom:create",
            "master:bom_item:read",
            "master:machine:read",
        },
        "must_not_have": {
            "business:quote:approve",
            "business:quote:create",
            "platform:config:read",
            "system:user:read",
        },
    },
    "workshop01": {
        "must_have": {
            "dashboard:view",
            "business:quote:read",
            "business:workshop:read",
            "business:mes:read",
        },
        "must_not_have": {
            "business:quote:create",
            "master:bom:create",
            "business:quote:approve",
            "platform:config:read",
        },
    },
    "finance01": {
        "must_have": {
            "business:quote:read",
            "business:quote:export",
            "business:accounting:read",
            "business:accounting:create",
        },
        "must_not_have": {
            "business:quote:create",
            "business:quote:approve",
            "master:bom:create",
            "platform:config:read",
        },
    },
    "approver01": {
        "must_have": {"business:quote:read", "business:quote:approve"},
        "must_not_have": {
            "business:quote:create",
            "master:bom:create",
            "platform:config:read",
            "system:user:read",
        },
    },
    "boss": {
        "must_have": {"dashboard:view", "business:quote:approve", "business:quote:read"},
        "must_not_have": {"platform:config:read", "system:user:read"},
    },
    "trialadmin": {
        "must_have": {
            "business:quote:read",
            "platform:notification:read",
            "business:settings:read",
            "business:settings:update",
        },
        "must_not_have": {"platform:config:read", "system:user:read"},
        "not_superuser": True,
    },
}


def _check(username: str, perms: set[str], is_superuser: bool) -> list[str]:
    issues: list[str] = []
    spec = ROLE_EXPECTATIONS.get(username)
    if spec is None:
        return [f"{username}: no expectation defined (skipped)"]

    if spec.get("not_superuser") and is_superuser:
        issues.append(f"{username}: must not be superuser")

    for code in spec.get("must_have", set()):
        if code not in perms and not is_superuser:
            issues.append(f"{username}: missing required permission {code}")

    for code in spec.get("must_not_have", set()):
        if code in perms or is_superuser:
            issues.append(f"{username}: must NOT have permission {code}")

    if not is_superuser:
        forbidden_hit = perms & FORBIDDEN_FOR_TRIAL
        if forbidden_hit:
            issues.append(f"{username}: forbidden permissions present: {sorted(forbidden_hit)}")

    return issues


def verify() -> int:
    failures: list[str] = []
    print_db_target()
    engine = create_engine(database_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    with SessionLocal() as db:
        for username in ROLE_EXPECTATIONS:
            user = (
                db.execute(
                    select(User)
                    .where(User.username == username)
                    .options(selectinload(User.roles).selectinload(Role.permissions))
                )
            ).scalar_one_or_none()
            if user is None:
                failures.append(f"{username}: user not found — run setup_trial_users.py")
                continue
            perms = collect_permission_codes(user)
            failures.extend(_check(username, perms, user.is_superuser))
            print(f"[{username}] permissions ({len(perms)}): {', '.join(sorted(perms)[:8])}{'...' if len(perms) > 8 else ''}")

        admin = db.execute(select(User).where(User.username == "admin")).scalar_one_or_none()
        if admin and not admin.is_superuser:
            failures.append("admin: expected is_superuser=True from bootstrap")

    print("\n--- Permission verification ---")
    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        print(f"\n{len(failures)} issue(s)")
        return 1
    print("All checks passed.")
    return 0


def main() -> None:
    sys.exit(verify())


if __name__ == "__main__":
    main()
