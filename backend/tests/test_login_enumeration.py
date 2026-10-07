"""A failed login must cost the same whether or not the username exists.

Round 223 read `authenticate_user` and found the classic enumeration oracle:

    user = await get_user_by_username(db, username)
    if user is None:
        return None                     # <-- skipped bcrypt, the only expensive step
    valid = await asyncio.to_thread(verify_password, password, user.hashed_password)

**bcrypt is deliberately slow**, so a nonexistent username answered in the time of one indexed query while a wrong
password paid the full cost. The endpoint's *message* was already symmetric — both cases raise
`401 "Incorrect username or password"` — **so the leak was entirely in the timing**, which is why it went unnoticed
through every round that read the endpoint's status codes.

**The fix is a dummy verification against a hash whose preimage nobody holds.** This test asserts the **call count**
rather than a duration: timing assertions are flaky in CI, while "the expensive step ran in both cases, exactly once" is
deterministic and is the property that actually matters.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

pytestmark = pytest.mark.asyncio


class _User:
    username = "real"
    hashed_password = "$2b$12$notarealhashnotarealhashnotarealhashnotarealhashnotarealhashno"


async def _authenticate(monkeypatch, user, password="whatever"):
    from app.services import auth_service

    calls: list[str] = []

    def _fake_verify(plain, hashed):
        calls.append(hashed)
        return False

    async def _fake_lookup(db, username):
        return user

    monkeypatch.setattr(auth_service, "verify_password", _fake_verify)
    monkeypatch.setattr(auth_service, "get_user_by_username", _fake_lookup)
    result = await auth_service.authenticate_user(object(), "someone", password)
    return result, calls


async def test_a_nonexistent_username_still_pays_the_verification_cost(monkeypatch):
    result, calls = await _authenticate(monkeypatch, None)

    assert result is None, "a nonexistent username must not authenticate"
    assert len(calls) == 1, (
        "the nonexistent-username path skipped the password verification. **That is a username-enumeration oracle**: "
        "bcrypt is deliberately slow, so the two failure paths become distinguishable by how long they take, even "
        f"though their status codes and messages are identical. Verifications ran: {len(calls)}"
    )


async def test_a_wrong_password_costs_the_same_as_a_missing_username(monkeypatch):
    missing, missing_calls = await _authenticate(monkeypatch, None)
    wrong, wrong_calls = await _authenticate(monkeypatch, _User())

    assert missing is None and wrong is None
    assert len(missing_calls) == len(wrong_calls), (
        f"the two failure paths run the verification {len(missing_calls)} and {len(wrong_calls)} times, so they are "
        "distinguishable by cost"
    )
    assert missing_calls != wrong_calls, (
        "both paths verified against the same hash. **A nonexistent username must not verify against anything a caller "
        "could satisfy**, so its dummy hash has to differ from every real one"
    )


def test_the_dummy_hash_is_a_bcrypt_hash_of_no_known_value():
    """Generated at import rather than hardcoded, and shaped like a real hash so the cost matches."""
    from app.services import auth_service

    dummy = auth_service._DUMMY_HASH
    assert dummy.startswith("$2"), f"the dummy hash is not a bcrypt hash, so its cost will not match: {dummy[:12]!r}"
    assert dummy != _User.hashed_password
    from app.core.security import verify_password

    for guess in ("", "password", "admin", "123456", "secret"):
        assert not verify_password(guess, dummy), f"the dummy hash accepts {guess!r}, which would authenticate anyone"
