"""A failed login has to be recorded, and the record must not contain the password.

Round 237 measured item ④ of the decision list — rate limiting — and found **zero** matches for any throttling, lockout or
attempt-counter machinery anywhere in the backend, no such package declared, and **`auth_service.py` without a logger at
all**. **A failed credential check was recorded nowhere**, so an operator had no way to notice an attack in progress.

**That splits the item in two, and only one half is a decision.** How many failures are too many, over what window, and
whether to delay or lock, is a product choice. **Recording that a failure happened is not** — it needs no policy, no
dependency and no behaviour change, and its absence is not a trade-off.

**And the response must stay what round 223 made it**: the two failure paths log *which* case it was, because the log is
read by operators rather than by attackers, while the response to the caller remains identical.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

pytestmark = pytest.mark.asyncio

PASSWORD = "correct-horse-battery-staple"
USERNAME = "probe-user"


class _User:
    username = USERNAME
    hashed_password = "$2b$12$notarealhashnotarealhashnotarealhashnotarealhashnotarealhashno"


async def _attempt(monkeypatch, user):
    from app.services import auth_service

    async def _lookup(db, username):
        return user

    def _reject(plain, hashed):
        return False

    monkeypatch.setattr(auth_service, "get_user_by_username", _lookup)
    monkeypatch.setattr(auth_service, "verify_password", _reject)
    return await auth_service.authenticate_user(object(), USERNAME, PASSWORD)


async def test_both_failure_paths_log_exactly_one_warning(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger="app.services.auth_service"):
        assert await _attempt(monkeypatch, None) is None
        assert await _attempt(monkeypatch, _User()) is None

    records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(records) == 2, (
        f"**a failed login produced {len(records)} warnings instead of one per attempt** — without a record, an operator "
        "cannot notice an attack in progress. **Recording that a failure happened is not a policy decision**: it is the "
        "half of the rate-limiting item that has no trade-off."
    )
    assert {r.name for r in records} == {"app.services.auth_service"}


async def test_the_log_never_contains_the_password(monkeypatch, caplog):
    with caplog.at_level(logging.WARNING, logger="app.services.auth_service"):
        await _attempt(monkeypatch, None)
        await _attempt(monkeypatch, _User())

    for record in caplog.records:
        rendered = record.getMessage()
        assert PASSWORD not in rendered, (
            "**the password reached the log.** A log is written to disk, shipped and read by more people than the "
            f"database: {rendered!r}"
        )
        assert USERNAME in rendered, "the log does not name the account, so it cannot be acted on"


async def test_the_caller_still_cannot_tell_the_two_cases_apart(monkeypatch):
    """Round 223's property, restated here because these two paths are now also the log's two cases."""
    missing = await _attempt(monkeypatch, None)
    wrong = await _attempt(monkeypatch, _User())

    assert missing is None and wrong is None, (
        "the two failure paths return different things, so the **response** distinguishes an existing account from a "
        "missing one — which is the enumeration oracle round 223 closed"
    )
