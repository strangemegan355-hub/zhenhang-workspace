"""The realtime fan-out and the envelope contract — the layer above the ACL, and it had no test either.

Round 156 pinned **who may receive** an envelope (`acl.py`). Measured next: **all five `push_*` functions in
`publish.py` are called by no test**, and that module opens its **own** `AsyncSessionLocal`, so it belongs in the
integration suite. **The two layers underneath it are pure or in-process and were equally untested:**

* `envelope.py` (51 lines) builds the messages the two Vite apps' realtime bridge consumes;
* `hub.py` (67 lines) is the in-process fan-out — **and getting the fan-out wrong means delivering one user's event to
  another**, which is why this is not merely a convenience test.

Two behaviours are **asserted as documented rather than blessed**:

* an unknown channel is **silently rewritten to `notification`** by `build_event_envelope`, so a typo turns into "needs
  the notification permission" instead of a failure;
* a queue that is **full drops the event and does not block** the publisher — a liveness property, not an oversight.
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

from app.realtime.envelope import (
    CHANNELS,
    EVENT_VERSION,
    PROTOCOL_VERSION,
    build_event_envelope,
    build_heartbeat_envelope,
    build_subscribe_ack,
)
from app.realtime.hub import UserRealtimeHub, get_realtime_hub


def _drain(queue: asyncio.Queue) -> list[dict]:
    items: list[dict] = []
    while not queue.empty():
        items.append(queue.get_nowait())
    return items


# --- envelope.py ---------------------------------------------------------------------------------------------


def test_an_event_envelope_carries_the_protocol_the_clients_expect():
    envelope = build_event_envelope(channel="quote", kind="quote.updated", payload={"quote_id": "q-1"})
    assert envelope["protocol_version"] == PROTOCOL_VERSION
    assert envelope["event_version"] == EVENT_VERSION
    assert envelope["message_type"] == "event"
    assert envelope["channel"] == "quote"
    assert envelope["payload"] == {"kind": "quote.updated", "quote_id": "q-1"}
    assert envelope["event_id"]
    assert envelope["timestamp"]


def test_each_envelope_gets_its_own_event_id():
    first = build_event_envelope(channel="quote", kind="a", payload={})
    second = build_event_envelope(channel="quote", kind="a", payload={})
    assert first["event_id"] != second["event_id"], "envelopes share an id, so a client cannot deduplicate them"


def test_an_unknown_channel_is_silently_rewritten_to_notification():
    """Asserted as it behaves: a typo becomes a permission question rather than an error."""
    envelope = build_event_envelope(channel="not-a-channel", kind="x", payload={})
    assert envelope["channel"] == "notification", (
        "the unknown-channel fallback changed; if it now raises or keeps the bad channel, update this test and the "
        "docstring in app/realtime/envelope.py"
    )
    for channel in CHANNELS:
        assert build_event_envelope(channel=channel, kind="x", payload={})["channel"] == channel


def test_the_heartbeat_and_subscribe_ack_are_well_formed():
    heartbeat = build_heartbeat_envelope()
    assert heartbeat["message_type"] == "heartbeat"
    assert heartbeat["payload"]["interval_ms"] > 0

    ack = build_subscribe_ack(["quote", "workflow"])
    assert ack["message_type"] == "subscribe_ack"
    assert ack["payload"] == {"channels": ["quote", "workflow"], "ok": True}
    assert ack["channel"] == "quote", "the ack reports its first requested channel"

    empty = build_subscribe_ack([])
    assert empty["channel"] == "notification", "an empty subscription still needs a channel a client can accept"


# --- hub.py --------------------------------------------------------------------------------------------------


async def test_a_user_only_receives_its_own_events():
    """The direction that matters: one user's envelope must not reach another user's queue."""
    hub = UserRealtimeHub()
    alice, bob = uuid4(), uuid4()
    alice_queue = await hub.subscribe(alice)
    bob_queue = await hub.subscribe(bob)

    await hub.publish_user(alice, {"for": "alice"})

    assert _drain(alice_queue) == [{"for": "alice"}]
    assert _drain(bob_queue) == [], "an event addressed to one user was delivered to another"


async def test_every_connection_of_one_user_receives_the_event():
    hub = UserRealtimeHub()
    user = uuid4()
    first = await hub.subscribe(user, transport="ws")
    second = await hub.subscribe(user, transport="sse")

    await hub.publish_user(user, {"n": 1})

    assert _drain(first) == [{"n": 1}]
    assert _drain(second) == [{"n": 1}], "a second connection of the same user missed the event"


async def test_publish_all_reaches_every_subscriber():
    hub = UserRealtimeHub()
    queues = [await hub.subscribe(uuid4()) for _ in range(3)]
    await hub.publish_all({"broadcast": True})
    assert all(_drain(q) == [{"broadcast": True}] for q in queues)


async def test_unsubscribing_stops_delivery_and_prunes_the_user():
    hub = UserRealtimeHub()
    user = uuid4()
    queue = await hub.subscribe(user)
    await hub.unsubscribe(user, queue)

    await hub.publish_user(user, {"after": "unsubscribe"})
    assert _drain(queue) == [], "an unsubscribed connection still received an event"
    assert user not in hub._queues, "the hub kept an empty entry for a user with no connections"


async def test_a_full_queue_drops_the_event_instead_of_blocking_the_publisher():
    """A liveness property: one slow client must not stall the fan-out for everyone."""
    hub = UserRealtimeHub()
    user = uuid4()
    queue = await hub.subscribe(user)
    assert queue.maxsize == 200

    for index in range(200):
        queue.put_nowait({"n": index})
    await asyncio.wait_for(hub.publish_user(user, {"overflow": True}), timeout=5.0)

    drained = _drain(queue)
    assert len(drained) == 200, "the full queue grew, so the bound is not enforced"
    assert {"overflow": True} not in drained, "an event was delivered past the queue's bound"


def test_the_hub_is_a_process_wide_singleton():
    """Pinned because it is what makes the fan-out reach every connection in this process — and what a test must not
    assume is empty."""
    assert get_realtime_hub() is get_realtime_hub()
