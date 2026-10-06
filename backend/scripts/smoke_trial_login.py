"""Quick login smoke test for trial accounts."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

# A trial runs on a server, not on the machine running this, so the host is overridable.
BASE = os.getenv("ERP_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
# username, environment variable holding that account's password. These used to be literals,
# which made this file a credential list; accounts without the variable are reported as skipped.
ACCOUNTS = [
    ("boss", "TRIAL_BOSS_PASSWORD"),
    ("sales01", "TRIAL_SALES_PASSWORD"),
    ("tech01", "TRIAL_TECH_PASSWORD"),
    ("workshop01", "TRIAL_WORKSHOP_PASSWORD"),
    ("finance01", "TRIAL_FINANCE_PASSWORD"),
    ("approver01", "TRIAL_APPROVER_PASSWORD"),
]


def login(username: str, password: str) -> tuple[bool, str]:
    body = json.dumps({"username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/v1/auth/login",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        token = data.get("data", {}).get("access_token") or data.get("access_token")
        if not token:
            return False, "no token in response"
        me_req = urllib.request.Request(
            f"{BASE}/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(me_req, timeout=10) as me_resp:
            me = json.loads(me_resp.read().decode())
        perms = me.get("data", {}).get("permissions") or me.get("permissions") or []
        return True, f"OK — {len(perms)} permissions"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


def main() -> int:
    failed = 0
    checked = 0
    for user, env_var in ACCOUNTS:
        password = os.getenv(env_var, "")
        if not password:
            print(f"[SKIP] {user}: set {env_var} to include this account")
            continue
        checked += 1
        ok, msg = login(user, password)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {user}: {msg}")
        if not ok:
            failed += 1
    if checked == 0:
        print("nothing checked: no TRIAL_*_PASSWORD variable is set")
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
