"""Every error path must answer in the envelope the clients decode.

The API answers with `error_response(message, code=...)`. Tests asserted 200/404/403/201/400/401/202/409 and **never
422** — the status FastAPI raises by itself before any application code runs. The hypothesis going in was that this path
was uncustomised and would answer `{"detail": [...]}`, leaving a client that decodes `{code, message, data}` with
nothing to show.

**Asking the running app settled it the other way.** Measured in-process:

    404 unknown route      {"code": "HTTP_ERROR", "message": "Request failed", "data": null, "detail": {...}}
    401 no token           same four keys
    422 missing body       same four keys, with the validation errors nested under "detail"

So the envelope **is** uniform, and this file pins that — because the shape is a contract the two Vite apps and the
Next.js admin all decode, and a change to it would be silent on the server side.

One behaviour is pinned explicitly because it is a choice rather than an accident: `code` is always `HTTP_ERROR` and
`message` is always `Request failed` for HTTP-layer faults, with the specific reason nested in `detail`. A client that
displays `message` alone will show the same sentence for a 404, a 401 and a 422.
"""

from __future__ import annotations

import json
import os

os.environ.setdefault("SECRET_KEY", "integration-baseline-secret-key-32chars")

import httpx  # noqa: E402
import pytest  # noqa: E402
from app.main import app  # noqa: E402

ENVELOPE_KEYS = {"code", "message", "data"}


async def _client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://integration")


def _assert_envelope(response, expected_status: int) -> dict:
    """Accept either an `httpx.Response` or the `JSONResponse` a handler returns directly.

    The handler is called directly in the third test, and a Starlette `JSONResponse` has no `.json()` — the first run of
    this file failed on exactly that.
    """
    assert response.status_code == expected_status, getattr(response, "text", "")[:300]
    if isinstance(response, httpx.Response):
        body = response.json()
    else:
        body = json.loads(response.body)
    assert isinstance(body, dict), f"the error body is not an object: {body!r}"
    assert ENVELOPE_KEYS <= set(body), (
        f"a {expected_status} answer is missing part of the envelope the clients decode: {sorted(body)}"
    )
    assert body["data"] is None
    return body


@pytest.mark.asyncio
async def test_a_validation_error_uses_the_same_envelope_as_every_other_error():
    """The path nothing asserted: FastAPI raises 422 before any application code runs."""
    async with await _client() as client:
        for label, kwargs in (
            ("no body", {}),
            ("empty object", {"json": {}}),
            ("wrong types", {"json": {"username": 12345, "password": ["not", "a", "string"]}}),
        ):
            response = await client.post("/api/v1/auth/login", **kwargs)
            body = _assert_envelope(response, 422)
            assert body["code"] == "HTTP_ERROR", f"{label}: {body}"
            assert body["message"] == "Request failed", f"{label}: {body}"
            assert "detail" in body, f"{label}: the specific validation errors were dropped entirely"


@pytest.mark.asyncio
async def test_a_missing_route_and_a_missing_token_use_the_same_envelope():
    async with await _client() as client:
        not_found = _assert_envelope(await client.get("/api/v1/definitely-not-a-route"), 404)
        assert not_found["code"] == "HTTP_ERROR"

        unauthenticated = _assert_envelope(await client.get("/api/v1/users"), 401)
        assert unauthenticated["code"] == "HTTP_ERROR"
        # The reason survives in `detail`, which is what makes the uniform envelope usable.
        assert "detail" in unauthenticated and unauthenticated["detail"], unauthenticated


@pytest.mark.asyncio
async def test_a_domain_error_keeps_its_own_code_and_message():
    """Business exceptions must NOT be flattened into `HTTP_ERROR`; that is the whole point of the handler."""
    from app.core.exceptions import UniqueViolationException
    from app.main import business_exception_handler

    response = await business_exception_handler(None, UniqueViolationException("machine.machine_code", "INJ2-0001"))
    body = _assert_envelope(response, 409)
    assert body["code"] == "UNIQUE_VIOLATION", body
    assert "already exists" in body["message"], body
