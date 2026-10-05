"""Read/write and authorization baseline against the seeded integration database.

The schema tests answer "does the database have the right shape". These answer the next questions,
which only a live database with seeded accounts can: can the application's own session layer write
and read a row, does a seeded account authenticate, does its token open what its permissions allow,
does a refresh token stay useless as an access token, and is the admin plane out of its reach.

They need the baseline to have run first (migrations plus `bootstrap_admin.py` plus
`setup_trial_users.py`); the failure message says so rather than reporting a confusing 401.
"""

from __future__ import annotations

import os

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

NEEDS_SEED = (
    "run the baseline first, which migrates, bootstraps the admin, seeds the trial accounts and "
    "exports a throwaway password for them: "
    "powershell -NoProfile -ExecutionPolicy Bypass -File <workspace>\\phase2\\phase2_baseline.ps1"
)


def _trial_password() -> str:
    """Read the seeded account's password. No default: a literal here is a credential in the repo."""
    password = os.environ.get("TRIAL_SALES_PASSWORD", "")
    assert password, "TRIAL_SALES_PASSWORD is not set. " + NEEDS_SEED
    return password


async def test_a_row_round_trips_through_the_application_session():
    """Write and read through app.db.session, then roll back so the check leaves no residue."""
    from app.db.session import engine
    from app.models.department import Department

    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        try:
            session.add(Department(name="Integration Baseline", code="it-baseline"))
            await session.flush()
            found = (
                await session.execute(select(Department).where(Department.code == "it-baseline"))
            ).scalar_one()
            assert found.name == "Integration Baseline"
        finally:
            await session.close()
            await transaction.rollback()

    async with engine.connect() as connection:
        left_behind = (
            await connection.execute(select(Department).where(Department.code == "it-baseline"))
        ).scalar_one_or_none()
    assert left_behind is None, "the baseline must not litter the database it verifies"


async def _login(client: httpx.AsyncClient) -> dict:
    response = await client.post(
        "/api/v1/auth/login", json={"username": "sales01", "password": _trial_password()}
    )
    assert response.status_code == 200, f"{response.text[:400]}\n{NEEDS_SEED}"
    body = response.json()
    return body.get("data", body)


async def test_a_seeded_account_authenticates_and_reads_a_scoped_endpoint():
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        tokens = await _login(client)
        response = await client.get(
            "/api/v1/quotes", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

    assert response.status_code == 200, response.text[:400]
    body = response.json()
    page = body.get("data", body)
    assert "items" in page, f"unexpected page shape: {body!r}"


async def test_a_refresh_token_cannot_authenticate_the_api():
    """The token-type check, confirmed end to end rather than only in unit tests."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        tokens = await _login(client)
        response = await client.get(
            "/api/v1/quotes", headers={"Authorization": f"Bearer {tokens['refresh_token']}"}
        )

    assert response.status_code == 401, (
        "a refresh token authenticated a normal endpoint; the token-type check is not applied"
    )


async def test_a_trial_account_cannot_reach_the_admin_plane():
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        tokens = await _login(client)
        response = await client.get(
            "/api/v1/users", headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )

    assert response.status_code in (401, 403), (
        f"a trial account reached the admin plane: {response.status_code} {response.text[:300]}"
    )


async def test_an_unknown_credential_is_rejected():
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        response = await client.post(
            "/api/v1/auth/login", json={"username": "sales01", "password": "definitely-wrong"}
        )

    assert response.status_code in (400, 401), response.text[:300]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
