#!/usr/bin/env python3
"""§3.7 / §3.8 API acceptance — mobile approve path + workshop board/BOM.

Mirrors what Mobile (待审→通过) and Workshop (打开报价→BOM/KPI) call.

Usage (API on :8000, BOOTSTRAP_ADMIN_PASSWORD set):
  python scripts/verify_mobile_workshop_flow.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any

DEFAULT_BASE = "http://127.0.0.1:8000"
LOGIN = {
    "username": os.getenv("VERIFY_ADMIN_USERNAME", "admin"),
    "password": os.getenv("BOOTSTRAP_ADMIN_PASSWORD", ""),
}
if not LOGIN["password"]:
    raise SystemExit("BOOTSTRAP_ADMIN_PASSWORD is required")


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
                raise RuntimeError(f"{method} {path} -> HTTP {status}: {raw[:600]}") from exc
            return self._unwrap(json.loads(raw) if raw else {})
        if status not in expected:
            raise RuntimeError(f"{method} {path} -> HTTP {status}: {raw[:600]}")
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


def _pick_customer(client: ApiClient) -> str:
    page = client._request("GET", "/api/v1/customers", params={"page": 1, "page_size": 5})
    items = page.get("items") or []
    if not items:
        raise RuntimeError("no customers — cannot create quote")
    return str(items[0]["id"])


def _pick_machine(client: ApiClient) -> str:
    page = client._request("GET", "/api/v1/machines", params={"page": 1, "page_size": 5})
    items = page.get("items") or []
    if not items:
        raise RuntimeError("no machines — cannot create quote")
    return str(items[0]["id"])


def _pick_product(client: ApiClient) -> str:
    page = client._request("GET", "/api/v1/products", params={"page": 1, "page_size": 5})
    items = page.get("items") or []
    if not items:
        raise RuntimeError("no products — cannot create quote (K-005 requires product_id)")
    return str(items[0]["id"])


def _ensure_reviewing_quote(client: ApiClient) -> dict:
    page = client._request("GET", "/api/v1/quotes", params={"page": 1, "page_size": 50})
    for item in page.get("items") or []:
        if str(item.get("workflow_state")) == "reviewing":
            print(f"  [ok] reuse reviewing quote {item.get('quote_no')} ({item['id']})")
            return item

    # Prefer an existing draft we can submit
    for item in page.get("items") or []:
        if str(item.get("workflow_state")) == "draft":
            quote_id = str(item["id"])
            result = client._request(
                "POST",
                f"/api/v1/quotes/{quote_id}/actions/transition",
                body={"action_code": "submit", "comment": "§3.7 submit draft"},
            )
            state = str(result.get("workflow_state") or "")
            if state == "reviewing":
                print(f"  [ok] submitted existing draft {item.get('quote_no')} → reviewing")
                return {"id": quote_id, "quote_no": item.get("quote_no"), "workflow_state": state}

    customer_id = _pick_customer(client)
    product_id = _pick_product(client)
    machine_id = _pick_machine(client)
    suffix = uuid.uuid4().hex[:8].upper()
    quote_no = f"MW-{suffix}"
    created = client._request(
        "POST",
        "/api/v1/quotes",
        body={
            "quote_no": quote_no,
            "title": f"Mobile/Workshop verify {suffix}",
            "customer_id": customer_id,
            "product_id": product_id,
            "machine_id": machine_id,
            "currency": "CNY",
        },
        expected=(201, 200),
    )
    quote_id = str(created["id"])
    print(f"  [ok] created draft {quote_no} ({quote_id})")

    # Minimal line so approve path is realistic
    client._request(
        "POST",
        "/api/v1/quotes/versions",
        body={
            "quote_id": quote_id,
            "items": [
                {
                    "item_code": "MW-LINE-1",
                    "item_name": "验收物料",
                    "unit": "pcs",
                    "quantity": "1",
                    "unit_price": "100",
                    "source_type": "manual",
                }
            ],
        },
        expected=(201,),
    )
    print("  [ok] saved version with 1 line")

    result = client._request(
        "POST",
        f"/api/v1/quotes/{quote_id}/actions/transition",
        body={"action_code": "submit", "comment": "§3.7 submit for mobile"},
    )
    state = str(result.get("workflow_state") or "")
    if state != "reviewing":
        raise RuntimeError(f"expected reviewing after submit, got {state}")
    print(f"  [ok] submitted → {state}")
    return {"id": quote_id, "quote_no": quote_no, "workflow_state": state}


def run() -> None:
    base = os.getenv("VERIFY_BASE_URL", DEFAULT_BASE)
    client = ApiClient(base)
    print("\n=== §3.7 / §3.8 Mobile + Workshop Verification ===\n")

    client.login()

    print("--- Mobile path (待审 → 通过) ---")
    quote = _ensure_reviewing_quote(client)
    quote_id = str(quote["id"])

    # Same list filter Mobile UI uses: quotes page then filter reviewing
    page = client._request("GET", "/api/v1/quotes", params={"page": 1})
    reviewing = [q for q in (page.get("items") or []) if str(q.get("workflow_state")) == "reviewing"]
    if not any(str(q["id"]) == quote_id for q in reviewing):
        raise RuntimeError("created reviewing quote not visible in quotes list")
    print(f"  [ok] mobile pending list contains target · count={len(reviewing)}")

    approved = client._request(
        "POST",
        f"/api/v1/quotes/{quote_id}/actions/transition",
        body={"action_code": "approve", "comment": "§3.7 mobile approve"},
    )
    if str(approved.get("workflow_state")) != "approved":
        raise RuntimeError(f"approve failed: {approved}")
    print(f"  [ok] mobile approve → {approved.get('workflow_state')}")

    print("\n--- Workshop path (看板 → 打开报价 → BOM/KPI) ---")
    board = client._request("GET", "/api/v1/workshop/board")
    live = board.get("live_quotes") or []
    production = board.get("production") or {}
    pipeline = production.get("quote_pipeline") or []
    oee = board.get("oee") or {}
    print(
        f"  [ok] board · live_quotes={len(live)} · pipeline={len(pipeline)} · oee={oee.get('oee')}"
    )
    if not isinstance(live, list):
        raise RuntimeError("live_quotes missing")

    detail = client._request("GET", f"/api/v1/quotes/{quote_id}")
    print(f"  [ok] open quote {detail.get('quote_no')} · state={detail.get('workflow_state')}")
    # Prefer DEMO quote for BOM tree (machine-linked seed has items)
    demo_page = client._request("GET", "/api/v1/quotes", params={"page": 1, "q": "DEMO-Q-001"})
    demo = next((i for i in (demo_page.get("items") or []) if i.get("quote_no") == "DEMO-Q-001"), None)
    bom_quote = client._request("GET", f"/api/v1/quotes/{demo['id']}") if demo else detail
    bom_id = bom_quote.get("bom_id")
    if bom_id:
        bom = client._request(
            "GET",
            "/api/v1/boms/items",
            params={"bom_id": bom_id, "page": 1, "page_size": 100},
        )
        items = bom.get("items") or []
        print(f"  [ok] BOM items={len(items)} · quote={bom_quote.get('quote_no')}")
        if not items:
            raise RuntimeError("expected DEMO BOM items")
    else:
        print("  [ok] quote has no bom_id (empty BOM tree expected)")

    # KPI shape used by Workshop UI
    reviewing_kpi = next((p for p in pipeline if p.get("state") == "reviewing"), None)
    approved_kpi = next((p for p in pipeline if p.get("state") == "approved"), None)
    print(
        f"  [ok] KPI · reviewing={reviewing_kpi.get('count') if reviewing_kpi else 0} "
        f"· approved={approved_kpi.get('count') if approved_kpi else 0}"
    )

    # Page reachability for Vite apps (localhost / IPv6)
    for label, url in (
        ("mobile", "http://localhost:5174/"),
        ("workshop", "http://localhost:5175/"),
    ):
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"  [ok] {label} page HTTP {resp.status}")
        except Exception as exc:  # noqa: BLE001
            print(f"  [warn] {label} page unreachable ({exc}) — start npm run dev:mobile/workshop")

    print("\n=== Mobile + Workshop verification passed ===\n")


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:  # noqa: BLE001
        print(f"\nFAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
