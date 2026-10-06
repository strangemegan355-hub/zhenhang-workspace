"""Data scope, proven end to end on the seeded database rather than only in SQL.

Round 3 replaced two contradictory scope implementations with one `scope_predicate`, verified by
compiling the predicate and inspecting the emitted SQL. That proves the predicate is right; it does
not prove an endpoint applies it, that the caller's department is loaded, or that another
department's row is genuinely absent from a real response.

This does. It creates a second department with its own user and one project in each department, then
asks the API as two seeded accounts:

  * `sales01` (trial_sales, data_scope = department) must see its own department's project and not
    the other one;
  * `boss` (trial_boss, data_scope = all) must see both, which is what separates "scoping works"
    from "the endpoint hides everything from everyone".

Seeding and cleanup are plain async helpers called from each test, deliberately not a fixture: a
module-defined async fixture makes the first test of a file fail when the file is run on its own
under pytest-asyncio 0.24, while the same file passes inside the suite because an earlier test has
already created the event loop. A test that only passes in one ordering is not a test.
"""

from __future__ import annotations

import os

import httpx
import pytest
from sqlalchemy import delete, select

MARKER = "it-scope"
NEEDS_SEED = (
    "run the baseline first, which migrates, seeds the trial accounts and exports throwaway "
    "passwords for them: powershell -NoProfile -ExecutionPolicy Bypass -File "
    "<workspace>\\phase2\\phase2_baseline.ps1"
)


def _password(env_name: str) -> str:
    """No default: a literal here would be a credential in the repository."""
    value = os.environ.get(env_name, "")
    assert value, f"{env_name} is not set. {NEEDS_SEED}"
    return value


async def _login(client: httpx.AsyncClient, username: str, env_name: str) -> str:
    response = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": _password(env_name)}
    )
    assert response.status_code == 200, f"{response.text[:300]}\n{NEEDS_SEED}"
    body = response.json()
    return body.get("data", body)["access_token"]


async def _project_numbers(username: str, env_name: str) -> set[str]:
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        token = await _login(client, username, env_name)
        response = await client.get(
            "/api/v1/projects",
            params={"page": 1, "page_size": 100},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200, response.text[:400]
    body = response.json()
    page = body.get("data", body)
    return {str(item.get("project_no")) for item in page.get("items", [])}


async def _seed_two_departments() -> None:
    """One project created in the caller's department, one in a second department."""
    from app.core.security import get_password_hash
    from app.db.session import AsyncSessionLocal
    from app.models.department import Department
    from app.models.project import Project
    from app.models.user import User

    async with AsyncSessionLocal() as session:
        await _cleanup(session)  # a previous run that died mid-way must not block this one

        other_department = Department(name="Integration Scope Department", code=MARKER)
        session.add(other_department)
        await session.flush()

        other_user = User(
            username=MARKER,
            hashed_password=get_password_hash(_password("TRIAL_SALES_PASSWORD")),
            department_id=other_department.id,
        )
        session.add(other_user)
        await session.flush()

        sales = (
            await session.execute(select(User).where(User.username == "sales01"))
        ).scalar_one()

        session.add_all(
            [
                Project(
                    project_no=f"{MARKER}-MINE",
                    name="scope fixture, own department",
                    created_by=sales.id,
                ),
                Project(
                    project_no=f"{MARKER}-THEIRS",
                    name="scope fixture, other department",
                    created_by=other_user.id,
                ),
            ]
        )
        await session.commit()


async def _cleanup(session) -> None:
    from app.models.department import Department
    from app.models.project import Project
    from app.models.user import User

    await session.execute(delete(Project).where(Project.project_no.like(f"{MARKER}-%")))
    await session.execute(delete(User).where(User.username == MARKER))
    await session.execute(delete(Department).where(Department.code == MARKER))


async def _teardown() -> None:
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await _cleanup(session)
        await session.commit()


async def test_a_department_scoped_account_sees_only_its_own_department():
    await _seed_two_departments()
    try:
        numbers = await _project_numbers("sales01", "TRIAL_SALES_PASSWORD")
    finally:
        await _teardown()

    assert f"{MARKER}-MINE" in numbers, "the caller's own department's row is missing"
    assert f"{MARKER}-THEIRS" not in numbers, (
        "a department-scoped account received a row created in another department"
    )


async def test_an_all_scope_account_sees_both_departments():
    await _seed_two_departments()
    try:
        numbers = await _project_numbers("boss", "TRIAL_BOSS_PASSWORD")
    finally:
        await _teardown()

    assert {f"{MARKER}-MINE", f"{MARKER}-THEIRS"} <= numbers, (
        "an all-scope account should see every department, otherwise the scope check is simply "
        "hiding rows from everyone"
    )


async def _one_project_by_id(project_id: str, username: str, env_name: str) -> int:
    """GET a single project by id as `username`, returning only the status code."""
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://integration") as client:
        token = await _login(client, username, env_name)
        response = await client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    return response.status_code


async def _ids_of_seeded_projects() -> dict[str, str]:
    from app.db.session import AsyncSessionLocal
    from app.models.project import Project

    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(Project.project_no, Project.id).where(Project.project_no.like(f"{MARKER}-%"))
            )
        ).all()
    return {no: str(identifier) for no, identifier in rows}


async def test_a_single_object_of_another_department_is_not_found():
    """The list being scoped is not the same claim as one object being scoped.

    `test_a_department_scoped_account_sees_only_its_own_department` proves the **list** omits another department's row.
    Phase 3 also asks for **object-level** authorization, and that is what this proves: asking for the other
    department's row **by id** must answer **404** — not 403, which would confirm the row exists, and not 200.

    Two directions, so this cannot pass by hiding everything from everyone:

      * `sales01` (department scope) gets **200** for its own department's project and **404** for the other one;
      * `boss` (all scope) gets **200** for that same "other" project, which proves it exists and is reachable.
    """
    await _seed_two_departments()
    try:
        identifiers = await _ids_of_seeded_projects()
        mine = identifiers.get(f"{MARKER}-MINE")
        theirs = identifiers.get(f"{MARKER}-THEIRS")
        assert mine and theirs, f"the seed did not produce both projects: {sorted(identifiers)}"

        owner_status = await _one_project_by_id(mine, "sales01", "TRIAL_SALES_PASSWORD")
        other_status = await _one_project_by_id(theirs, "sales01", "TRIAL_SALES_PASSWORD")
        all_scope_status = await _one_project_by_id(theirs, "boss", "TRIAL_BOSS_PASSWORD")
    finally:
        await _teardown()

    assert owner_status == 200, (
        f"a department-scoped account was refused its own department's project by id (got {owner_status}); "
        "object scoping must not lock a caller out of its own rows"
    )
    assert other_status == 404, (
        f"another department's project answered {other_status} instead of 404 by id; 403 would confirm the row "
        "exists, and 200 would leak it"
    )
    assert all_scope_status == 200, (
        f"the other department's project answered {all_scope_status} to an all-scope account, so it is not "
        "reachable by anyone and the 404 above proves nothing"
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
