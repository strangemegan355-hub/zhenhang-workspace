"""The success envelope is the most-used contract in the system, and nothing asserted its shape.

Every successful response is `{"code": "SUCCESS", "message": "OK", "data": ...}` — the shape the two Vite apps and the
Next.js admin all decode, and the one every page route returns. Measured before writing this: the suite asserts
`code == "SUCCESS"` in a handful of places and reads `["data"]` widely, but **all three assertions on `["message"]` are
on error bodies** (`test_error_envelope.py` twice, `test_stage2_api.py` once) — so the success `message`, and the full
success key set, were never checked.

Round 161 pinned the **error** branch, including its 422. This pins the success branch, and one detail that matters for
clients: **`data` carries the page or the object whole**, so a paginated route answers
`{"code", "message", "data": {"total", "page", "page_size", "items"}}` — the envelope is **not** flattened into the page.
"""

from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "integration-baseline-secret-key-32chars")

import httpx  # noqa: E402
import pytest  # noqa: E402

from app.core.response import error_response, success_response  # noqa: E402
from app.main import app  # noqa: E402

ENVELOPE_KEYS = {"code", "message", "data"}
PAGE_KEYS = {"total", "page", "page_size", "items"}


def test_the_success_builder_produces_the_documented_envelope():
    body = success_response()
    assert set(body) == ENVELOPE_KEYS, body
    assert body["code"] == "SUCCESS"
    assert body["message"] == "OK"
    assert body["data"] is None

    # An explicit message and code pass through; a callable argument is not flattened by accident.
    custom = success_response({"id": 1}, message="Created", code="CREATED")
    assert custom == {"code": "CREATED", "message": "Created", "data": {"id": 1}}


def test_the_error_builder_only_adds_detail_when_there_is_some():
    """`detail` is optional, and its absence is part of the error contract pinned in the other file."""
    assert set(error_response("nope")) == ENVELOPE_KEYS
    assert "detail" in error_response("nope", detail={"field": "value"})


async def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://integration")


@pytest.mark.asyncio
async def test_a_real_route_answers_in_the_same_envelope():
    async with await _client() as client:
        response = await client.get("/api/v1/health/live")
    assert response.status_code == 200, response.text[:300]
    body = response.json()
    assert set(body) == ENVELOPE_KEYS, f"a successful response is missing part of the envelope: {sorted(body)}"
    assert body["code"] == "SUCCESS"
    assert body["message"] == "OK"
    assert isinstance(body["data"], dict) and body["data"], body


@pytest.mark.asyncio
async def test_a_paginated_route_nests_the_page_inside_data():
    """The page must arrive whole under `data`, not merged into the envelope."""
    login = None
    async with await _client() as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"username": "sales01", "password": os.environ.get("TRIAL_SALES_PASSWORD", "")},
        )
        assert login.status_code == 200, f"{login.text[:300]}"
        token = login.json()["data"]["access_token"]

        response = await client.get(
            "/api/v1/machines", params={"page": 1, "page_size": 5}, headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200, response.text[:300]
    body = response.json()
    assert set(body) == ENVELOPE_KEYS, sorted(body)
    assert PAGE_KEYS <= set(body["data"]), (
        f"the page is not nested under `data`; a client that reads `data.total` would break: {sorted(body['data'])}"
    )
