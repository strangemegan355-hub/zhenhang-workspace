#!/usr/bin/env python3
"""P2 end-to-end API verification — quote loop, notifications, export tasks.

Usage (from backend/ with API running on :8000):
  python scripts/verify_p2_flow.py
  python scripts/verify_p2_flow.py --base-url http://127.0.0.1:8000 --skip-export
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_BASE = "http://127.0.0.1:8000"
DEMO_QUOTE_NO = "DEMO-Q-001"
LOGIN = {
    "username": os.getenv("VERIFY_ADMIN_USERNAME", "admin"),
    "password": os.getenv("BOOTSTRAP_ADMIN_PASSWORD", ""),
}
if not LOGIN["password"]:
    raise SystemExit(
        "BOOTSTRAP_ADMIN_PASSWORD is required to run this flow check; no default password ships."
    )


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict | None = None,
        params: dict | None = None,
        expected: tuple[int, ...] = (200, 201, 202),
    ) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{qs}" if qs else url
        data = json.dumps(body).encode() if body is not None else None
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = resp.status
                raw = resp.read().decode()
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode()
            if status not in expected:
                raise RuntimeError(f"{method} {path} -> HTTP {status}: {raw[:500]}") from exc
            return self._unwrap(json.loads(raw) if raw else {})
        if status not in expected:
            raise RuntimeError(f"{method} {path} -> HTTP {status}: {raw[:500]}")
        return self._unwrap(json.loads(raw) if raw else {})

    @staticmethod
    def _unwrap(payload: Any) -> Any:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def login(self) -> None:
        data = self._request("POST", "/api/v1/auth/login", body=LOGIN, expected=(200,))
        self.token = data["access_token"]
        print("  [ok] login")

    def find_demo_quote(self) -> dict:
        page = self._request("GET", "/api/v1/quotes", params={"page": 1, "q": DEMO_QUOTE_NO})
        items = page.get("items") or []
        for item in items:
            if item.get("quote_no") == DEMO_QUOTE_NO:
                print(f"  [ok] found {DEMO_QUOTE_NO} ({item['id']})")
                return item
        raise RuntimeError(f"Quote {DEMO_QUOTE_NO} not found — run seed_demo_quote.py first")

    def quote_detail(self, quote_id: str) -> dict:
        detail = self._request("GET", f"/api/v1/quotes/{quote_id}")
        print(f"  [ok] quote detail · state={detail.get('workflow_state')} · items={len(detail.get('items') or [])}")
        return detail

    def save_version(self, quote_id: str, items: list[dict]) -> dict:
        payload_items = [
            {
                "item_code": i["item_code"],
                "item_name": i["item_name"],
                "spec": i.get("spec"),
                "unit": i["unit"],
                "quantity": str(i["quantity"]),
                "unit_price": str(i["unit_price"]),
                "source_type": i.get("source_type", "manual"),
            }
            for i in items
        ]
        version = self._request(
            "POST",
            "/api/v1/quotes/versions",
            body={"quote_id": quote_id, "items": payload_items},
            expected=(201,),
        )
        print(f"  [ok] saved version V{version.get('version_no')}")
        return version

    def version_diff(self, quote_id: str, from_v: int, to_v: int) -> dict:
        diff = self._request(
            "GET",
            f"/api/v1/quotes/{quote_id}/versions/diff",
            params={"from_version_no": from_v, "to_version_no": to_v},
        )
        print(f"  [ok] diff V{from_v}→V{to_v} · amount_change={diff.get('amount_change')}")
        return diff

    def workflow_actions(self, state: str) -> list[dict]:
        actions = self._request(
            "GET",
            "/api/v1/workflows/actions",
            params={"entity_type": "quote", "current_state": state},
        )
        codes = [a.get("action_code") for a in (actions or [])]
        print(f"  [ok] workflow actions @ {state}: {codes}")
        return actions or []

    def transition(self, quote_id: str, action_code: str, comment: str = "P2 verify") -> dict:
        result = self._request(
            "POST",
            f"/api/v1/quotes/{quote_id}/actions/transition",
            body={"action_code": action_code, "comment": comment},
        )
        print(f"  [ok] transition {action_code} -> {result.get('workflow_state')}")
        return result

    def export_quote(self, quote_id: str, fmt: str = "pdf") -> dict:
        task = self._request(
            "POST",
            f"/api/v1/quotes/{quote_id}/exports",
            body={"format": fmt},
            expected=(202,),
        )
        print(f"  [ok] export requested · task={task.get('id')} · status={task.get('status')}")
        return task

    def process_pending(self, event_type: str = "quote.export.requested") -> dict:
        result = self._request(
            "POST",
            "/api/v1/quotes/events/process-pending",
            body={},
            params={"event_type": event_type},
        )
        print(f"  [ok] process-pending · {result}")
        return result

    def poll_export_task(self, task_id: str, timeout_sec: float = 90.0) -> dict:
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            task = self._request("GET", f"/api/v1/quotes/exports/{task_id}")
            status = task.get("status")
            if status in {"completed", "failed"}:
                print(f"  [ok] export task {status} · file_id={task.get('file_id')}")
                if status == "failed":
                    raise RuntimeError(task.get("error_message") or "export failed")
                return task
            time.sleep(2)
        raise RuntimeError(f"export task {task_id} timed out after {timeout_sec}s")

    def unread_count(self) -> int:
        data = self._request("GET", "/api/v1/notifications/unread-count")
        count = int(data.get("unread", 0))
        print(f"  [ok] unread notifications: {count}")
        return count

    def list_notifications(self) -> list[dict]:
        page = self._request("GET", "/api/v1/notifications", params={"page": 1})
        items = page.get("items") or []
        print(f"  [ok] notifications listed: {len(items)}")
        return items

    def mark_read(self, notification_id: str) -> None:
        self._request("PATCH", f"/api/v1/notifications/{notification_id}/read", body={})
        print(f"  [ok] marked read {notification_id}")


def run_flow(base_url: str, skip_export: bool) -> None:
    client = ApiClient(base_url)
    print("\n=== P2 Business Flow Verification ===\n")

    client.login()
    quote = client.find_demo_quote()
    quote_id = str(quote["id"])
    detail = client.quote_detail(quote_id)
    state = str(detail.get("workflow_state") or "draft")

    items = detail.get("items") or []
    if items:
        bumped = [{**i, "quantity": float(i.get("quantity", 1)) + 0.01} for i in items[:3]]
        merged = [{**i} for i in items]
        for row in bumped:
            for idx, orig in enumerate(merged):
                if orig.get("item_code") == row["item_code"]:
                    merged[idx] = row
                    break
        version = client.save_version(quote_id, merged)
        to_v = int(version.get("version_no", 2))
        client.version_diff(quote_id, 1, to_v)
    else:
        print("  [warn] no quote items — skip version/diff")

    if state == "draft":
        actions = client.workflow_actions("draft")
        if any(a.get("action_code") == "submit" for a in actions):
            result = client.transition(quote_id, "submit")
            state = str(result.get("workflow_state") or "reviewing")
        else:
            print("  [warn] submit action unavailable")

    if state in {"reviewing", "submitted", "pending_approval"}:
        actions = client.workflow_actions(state)
        if any(a.get("action_code") == "approve" for a in actions):
            result = client.transition(quote_id, "approve")
            state = str(result.get("workflow_state") or "approved")
        else:
            print("  [warn] approve action unavailable — quote may need reset for re-run")

    if state != "approved" and not skip_export:
        print("  [warn] quote not approved — export may fail")

    unread_before = client.unread_count()

    if not skip_export:
        task = client.export_quote(quote_id, "pdf")
        task_id = str(task["id"])
        try:
            pending = client.process_pending("quote.export.requested")
            print(f"  [ok] process-pending · {pending}")
            if pending.get("processed", 0) == 0:
                print("  [info] waiting for event_worker to consume export task…")
        except RuntimeError as exc:
            print(f"  [warn] process-pending skipped: {exc}")
            print("  [info] waiting for event_worker to consume export task…")
        client.poll_export_task(task_id, timeout_sec=180.0)
        unread_after = client.unread_count()
        if unread_after < unread_before:
            print("  [warn] unread count did not increase after export (notifications may already exist)")
    else:
        print("  [skip] export flow")

    notes = client.list_notifications()
    unread = next((n for n in notes if not n.get("read_at")), None)
    if unread:
        client.mark_read(str(unread["id"]))
        final = client.unread_count()
        print(f"  [ok] unread after mark-read: {final}")

    print("\n=== P2 verification passed ===\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify P2 quote/notification/export flow")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--skip-export", action="store_true", help="Skip export + worker steps")
    args = parser.parse_args()
    try:
        run_flow(args.base_url, args.skip_export)
    except Exception as exc:
        print(f"\n=== P2 verification FAILED ===\n{exc}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
