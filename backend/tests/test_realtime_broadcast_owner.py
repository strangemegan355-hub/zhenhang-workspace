"""A broadcast that concerns one user must name them, because an ownerless one reaches everyone.

Round 194 recorded two fail-open branches in `app/realtime/acl.py` as **"asserted, not endorsed"**, and round 224 asked
whether they are reachable. They are:

* `quote_export_handlers.py:78` publishes with `owner_id=quote.created_by if quote else None` — **so a deleted or missing
  quote row produces `owner_id=None`**;
* `publish.push_quote_export_status` then sends a **broadcast** carrying that `owner_id`;
* and `acl._record_visible_to_user` returns `True` for an ownerless envelope at both `SELF` and `DEPARTMENT` scope, so the
  envelope reached **every** such viewer allowed on the channel — with a payload naming `quote_no`, `task_id` and
  `file_id` for an export that only one person requested.

**The export task belongs to the caller**, so the broadcast now falls back to `user_id`. This test asserts the property
rather than the expression: **no broadcast on the quote channel may be ownerless, and a real owner must still be kept.**
"""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

pytestmark = pytest.mark.asyncio

USER = uuid4()
TASK = uuid4()
QUOTE = uuid4()
OWNER = uuid4()


async def _publish(monkeypatch, **overrides):
    from app.realtime import publish

    calls: list[dict] = []

    async def _fake(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(publish, "push_realtime_event", _fake)
    await publish.push_quote_export_status(
        user_id=USER,
        task_id=TASK,
        quote_id=QUOTE,
        quote_no="Q-224",
        status="completed",
        file_id=None,
        **overrides,
    )
    return [call for call in calls if call.get("broadcast") and call.get("channel") == "quote"]


async def test_a_broadcast_with_no_owner_is_named_after_the_requester(monkeypatch):
    broadcasts = await _publish(monkeypatch, owner_id=None)

    assert broadcasts, "no broadcast on the quote channel was published, so this guard has lost its subject"
    for call in broadcasts:
        assert call.get("resource_owner_id") is not None, (
            "an ownerless broadcast is delivered to **every** SELF- or DEPARTMENT-scope viewer on the channel, because "
            "`acl._record_visible_to_user` returns True when the owner is None. **A broadcast about one person's export "
            "must name that person** — this is the path that makes round 194's documented fail-open reachable."
        )
        assert call["resource_owner_id"] == USER, (
            f"the fallback should be the requester ({USER}), not {call['resource_owner_id']}"
        )


async def test_a_known_owner_is_still_used(monkeypatch):
    broadcasts = await _publish(monkeypatch, owner_id=OWNER)

    assert broadcasts
    for call in broadcasts:
        assert call["resource_owner_id"] == OWNER, (
            "when the quote row exists its owner must be preserved, so the fallback only covers the missing-owner case"
        )
