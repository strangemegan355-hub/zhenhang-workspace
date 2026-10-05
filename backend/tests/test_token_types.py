"""A refresh token or realtime ticket must never work as an access token.

Regression test for the token-type confusion: the header authentication path used to decode a
JWT and look only at the signature and `sub`, so the long-lived refresh token authenticated
every route. These cases need no database.
"""

from __future__ import annotations

import pytest

from app.core.security import (
    create_access_token,
    create_realtime_ticket,
    create_refresh_token,
    decode_access_token,
    decode_realtime_ticket,
    decode_refresh_token,
)

SUBJECT = "11111111-1111-1111-1111-111111111111"


def test_access_token_is_accepted_as_an_access_token() -> None:
    payload = decode_access_token(create_access_token(SUBJECT))
    assert payload is not None
    assert payload["sub"] == SUBJECT
    assert payload["typ"] == "access"


def test_refresh_token_is_rejected_as_an_access_token() -> None:
    refresh = create_refresh_token(SUBJECT)
    assert decode_refresh_token(refresh) is not None
    assert decode_access_token(refresh) is None


def test_realtime_ticket_is_rejected_as_an_access_token() -> None:
    ticket = create_realtime_ticket(SUBJECT)
    assert decode_realtime_ticket(ticket) is not None
    assert decode_access_token(ticket) is None


def test_access_token_is_rejected_as_a_refresh_token() -> None:
    assert decode_refresh_token(create_access_token(SUBJECT)) is None


def test_access_token_is_rejected_as_a_realtime_ticket() -> None:
    assert decode_realtime_ticket(create_access_token(SUBJECT)) is None


def test_realtime_ticket_is_rejected_as_a_refresh_token() -> None:
    assert decode_refresh_token(create_realtime_ticket(SUBJECT)) is None


def test_ticket_does_not_outlive_its_short_ttl() -> None:
    from datetime import timedelta

    ticket = create_realtime_ticket(SUBJECT, expires_delta=timedelta(seconds=-1))
    assert decode_realtime_ticket(ticket) is None


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(SUBJECT)
    head, payload, signature = token.split(".")
    tampered = ".".join([head, payload, signature[:-2] + "xx"])
    assert decode_access_token(tampered) is None


def test_token_without_a_type_claim_is_rejected() -> None:
    """Tokens minted before the type check existed must not be grandfathered in."""
    from datetime import UTC, datetime, timedelta

    from jose import jwt

    from app.config.settings import settings

    legacy = jwt.encode(
        {"sub": SUBJECT, "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    assert decode_access_token(legacy) is None
