"""Quick login smoke test for trial accounts."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
ACCOUNTS = [
    ("boss", "Trial@Boss2026"),
    ("sales01", "Trial@Sales2026"),
    ("tech01", "Trial@Tech2026"),
    ("workshop01", "Trial@Workshop2026"),
    ("finance01", "Trial@Finance2026"),
    ("approver01", "Trial@Approver2026"),
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
    for user, pwd in ACCOUNTS:
        ok, msg = login(user, pwd)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {user}: {msg}")
        if not ok:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
