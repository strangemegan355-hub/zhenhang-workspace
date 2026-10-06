"""The enforcement point of functional authorization — `app/core/deps.py` — had no test of its own.

`require_permissions` guards the endpoint surface — each endpoint that needs a permission declares it in its own
signature — and `test_admin_plane.py` proves a 403 is returned somewhere, so
denial is covered behaviourally. What no test covered is **the branches**: the superuser bypass, the `*:*:*` wildcard,
the inactive-user gate, and — the one that matters most — **an access token offered where a realtime ticket is
required**, which is the confusion the ticket mechanism exists to prevent.

`security.py` is already covered by `test_token_types.py`, whose docstring records the bug that motivated it: checking
signatures only let **a refresh token be presented as an access token**. This file exercises the layer that consumes
those tokens.

Everything here uses the **real** models — `User`, `Role`, `Permission` — as unsaved objects, and the **real** token
functions, so nothing is a stand-in whose divergence could hide a defect. Measured first: an unsaved graph is enough,
and `collect_permission_codes` reads it correctly.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from app.config.settings import settings
from app.core.deps import (
    get_current_active_user,
    get_token_payload,
    require_any_permission,
    require_permissions,
    require_realtime_ticket,
)
from app.core.security import (
    create_access_token,
    create_realtime_ticket,
    create_refresh_token,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


def _user(*codes: str, is_superuser: bool = False, is_active: bool = True, roles: list[Role] | None = None) -> User:
    if roles is None:
        permissions = [Permission(code=code, name=code, resource=code.rsplit(":", 1)[0], action="read") for code in codes]
        roles = [Role(code="test_role", name="Test", data_scope="self", permissions=permissions)] if codes else []
    return User(
        username=f"u-{uuid4().hex[:8]}",
        hashed_password="x",
        is_superuser=is_superuser,
        is_active=is_active,
        roles=roles,
    )


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def _expect_http(coro, status_code: int) -> HTTPException:
    with pytest.raises(HTTPException) as raised:
        await coro
    assert raised.value.status_code == status_code, raised.value.detail
    return raised.value


# --- get_current_active_user ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_an_inactive_user_is_refused_with_403_and_an_active_one_is_returned():
    active = _user()
    assert await get_current_active_user(active) is active

    inactive = _user(is_active=False)
    error = await _expect_http(get_current_active_user(inactive), 403)
    assert error.detail == "Inactive user"


# --- require_permissions -------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_missing_permission_is_refused_and_named():
    dependency = require_permissions("business:quote:approve")
    allowed = _user("business:quote:approve")
    assert await dependency(allowed) is allowed

    refused = _user("business:quote:read")
    error = await _expect_http(dependency(refused), 403)
    assert error.detail["missing_permissions"] == ["business:quote:approve"], error.detail


@pytest.mark.asyncio
async def test_a_superuser_passes_a_permission_it_does_not_hold():
    dependency = require_permissions("platform:config:update")
    superuser = _user(is_superuser=True)  # holds no permission at all
    assert not superuser.roles
    assert await dependency(superuser) is superuser


# --- require_any_permission ----------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_any_of_the_listed_permissions_is_enough_and_the_wildcard_always_is():
    dependency = require_any_permission("business:quote:read", "business:quote:approve")

    first = _user("business:quote:read")
    assert await dependency(first) is first
    second = _user("business:quote:approve")
    assert await dependency(second) is second
    wildcard = _user("*:*:*")
    assert await dependency(wildcard) is wildcard


@pytest.mark.asyncio
async def test_having_none_of_the_listed_permissions_is_refused():
    dependency = require_any_permission("business:quote:read", "business:quote:approve")
    outsider = _user("master:material:read")
    error = await _expect_http(dependency(outsider), 403)
    assert error.detail["required_any"] == ["business:quote:read", "business:quote:approve"]


# --- require_realtime_ticket ---------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_realtime_ticket_authenticates_and_an_access_token_does_not():
    """The point of the ticket: it travels in a URL, so an access token must not work there."""
    subject = uuid4()
    ticket = create_realtime_ticket(subject)
    assert await require_realtime_ticket(ticket) == subject

    access = create_access_token(subject)
    await _expect_http(require_realtime_ticket(access), 401)
    refresh = create_refresh_token(subject)
    await _expect_http(require_realtime_ticket(refresh), 401)
    await _expect_http(require_realtime_ticket("not-a-token-at-all"), 401)


@pytest.mark.asyncio
async def test_an_expired_ticket_is_refused():
    expired = create_realtime_ticket(uuid4(), expires_delta=timedelta(seconds=-1))
    await _expect_http(require_realtime_ticket(expired), 401)


# --- get_token_payload ---------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_credentials_are_refused_with_401():
    await _expect_http(get_token_payload(None), 401)
    await _expect_http(get_token_payload(_credentials("")), 401)


@pytest.mark.asyncio
async def test_an_access_token_yields_its_subject_and_a_refresh_token_is_refused():
    subject = uuid4()
    payload = await get_token_payload(_credentials(create_access_token(subject)))
    assert payload["sub"] == str(subject)

    # A refresh token is validly signed and carries a subject; only the declared type separates them.
    await _expect_http(get_token_payload(_credentials(create_refresh_token(subject))), 401)


@pytest.mark.asyncio
async def test_a_token_signed_with_another_key_is_refused():
    foreign = jwt.encode({"sub": str(uuid4()), "typ": "access"}, "a-different-secret-key-entirely", algorithm=settings.algorithm)
    await _expect_http(get_token_payload(_credentials(foreign)), 401)


@pytest.mark.asyncio
async def test_an_expired_access_token_is_refused():
    expired = create_access_token(uuid4(), expires_delta=timedelta(seconds=-1))
    await _expect_http(get_token_payload(_credentials(expired)), 401)
