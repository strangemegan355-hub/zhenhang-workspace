"""The push channel's authorization had no test at all — pin it, including the two fail-open branches.

`app/realtime/acl.py` decides **which user may receive which event**. It is called from three places, including
`store.py`, so it also gates what gets persisted and replayed — and `can_deliver_envelope`, `build_acl_context`,
`allowed_channels`, `filter_subscribed_channels` and both private helpers were **called by no test anywhere**. The only
test imports of the realtime layer are `retention`, which is a different question.

The module is pure (`UUID`, `DataScope`, dict lookups), so this needs no server and no socket.

**Two branches fail open, and they are asserted as they are rather than blessed or called a vulnerability:**

  * in `_record_visible_to_user`, an envelope with **no owner** is delivered to `SELF` and to `DEPARTMENT`; and
  * the `DEPARTMENT` branch checks only that the **viewer** has a department — it does not compare the owner's.

Both are reachable only for **broadcast** envelopes, and the channel permission check has already run by then, so a
broadcast reaching every department-scoped user who may see that channel is arguably what "broadcast" means. **Pinning
the behaviour is the point: if either is ever tightened, this test says so.**
"""

from __future__ import annotations

from uuid import uuid4

from app.core.data_scope import DataScope
from app.realtime.acl import (
    CHANNEL_PERMISSIONS,
    RealtimeACLContext,
    can_deliver_envelope,
    filter_subscribed_channels,
)


def _ctx(**overrides) -> RealtimeACLContext:
    """A context that may use the `notification` channel, so a test exercises the **scope** logic.

    The channel gate runs first in `can_deliver_envelope`, so a context with no permissions is refused there and would
    make every scope assertion pass for the wrong reason. Tests about the channel gate pass `permissions=frozenset()`.
    """
    base = dict(
        user_id=uuid4(),
        permissions=frozenset({"platform:notification:read"}),
        data_scope=DataScope.SELF,
        department_id=None,
        tenant_id=None,
        role_codes=frozenset(),
        is_superuser=False,
    )
    base.update(overrides)
    return RealtimeACLContext(**base)


def _envelope(channel: str = "notification", **payload) -> dict:
    return {"channel": channel, "message_type": "event", "payload": payload}


def test_a_user_without_the_channel_permission_is_refused_and_a_user_with_it_is_not():
    """Both directions, so "everything is refused" cannot pass this file."""
    without = _ctx(permissions=frozenset())
    with_it = _ctx(permissions=frozenset({"platform:notification:read"}))

    assert not can_deliver_envelope(without, _envelope())
    assert can_deliver_envelope(with_it, _envelope())


def test_superuser_and_the_wildcard_permission_receive_every_channel():
    for ctx in (_ctx(is_superuser=True), _ctx(permissions=frozenset({"*:*:*"}))):
        for channel in CHANNEL_PERMISSIONS:
            assert can_deliver_envelope(ctx, _envelope(channel)), channel


def test_the_workshop_role_shortcut_grants_three_channels_without_permissions():
    """`WORKSHOP_ROLE_CODES` members receive quote, workflow and audit — a grant worth pinning explicitly."""
    ctx = _ctx(role_codes=frozenset({"workshop"}), permissions=frozenset())
    for channel in ("quote", "workflow", "audit"):
        assert can_deliver_envelope(ctx, _envelope(channel)), channel
    assert not can_deliver_envelope(ctx, _envelope("notification")), (
        "the workshop shortcut must not become a grant of every channel"
    )


def test_the_channel_gate_runs_before_the_scope_logic():
    """Ordering worth pinning: a scope-correct envelope is still refused on a channel the user may not use."""
    no_channels = _ctx(permissions=frozenset(), data_scope=DataScope.ALL)
    assert not can_deliver_envelope(no_channels, _envelope(owner_id=str(uuid4())))
    assert can_deliver_envelope(_ctx(data_scope=DataScope.ALL), _envelope(owner_id=str(uuid4())))


def test_a_targeted_notification_reaches_only_its_recipient():
    recipient = _ctx(permissions=frozenset({"platform:notification:read"}))
    someone_else = _ctx(permissions=frozenset({"platform:notification:read"}))
    envelope = _envelope(kind="notification.new")

    assert can_deliver_envelope(recipient, envelope, audience="user", audience_user_id=recipient.user_id)
    assert not can_deliver_envelope(
        someone_else, envelope, audience="user", audience_user_id=recipient.user_id
    ), "a notification addressed to one user was deliverable to another"


def test_heartbeats_are_delivered_before_the_audience_check():
    """Deliberate: a heartbeat carries no record, and refusing it would break the connection's own keepalive."""
    ctx = _ctx(permissions=frozenset({"platform:notification:read"}))
    for message_type in ("heartbeat", "heartbeat_ack", "subscribe_ack"):
        envelope = {"channel": "notification", "message_type": message_type, "payload": {}}
        assert can_deliver_envelope(ctx, envelope, audience="user", audience_user_id=uuid4()), message_type

    # But the channel check still runs first: a heartbeat on a channel this user may not use is refused.
    other = _ctx(permissions=frozenset())
    assert not can_deliver_envelope(other, {"channel": "notification", "message_type": "heartbeat", "payload": {}})


def test_self_scope_delivers_its_own_records_and_not_another_users():
    mine, theirs = uuid4(), uuid4()
    ctx = _ctx(data_scope=DataScope.SELF, user_id=mine)
    envelope = _envelope(owner_id=str(mine))

    assert can_deliver_envelope(ctx, envelope, resource_owner_id=mine)
    assert not can_deliver_envelope(ctx, envelope, resource_owner_id=theirs)


def test_the_two_fail_open_branches_behave_as_documented():
    """Asserted, not endorsed: an ownerless broadcast, and a department scope that never compares departments."""
    self_scope = _ctx(data_scope=DataScope.SELF)
    department_scope = _ctx(data_scope=DataScope.DEPARTMENT, department_id=uuid4())
    other_department = uuid4()

    ownerless = _envelope()
    assert can_deliver_envelope(self_scope, ownerless), (
        "SELF scope now refuses an ownerless envelope; if that is deliberate, update this test and the docstring in "
        "app/realtime/acl.py"
    )
    assert can_deliver_envelope(department_scope, ownerless)
    # The department branch checks the viewer's department, not the owner's, so another department's owner still passes.
    assert can_deliver_envelope(department_scope, _envelope(owner_id=str(uuid4())), resource_owner_id=uuid4())
    assert other_department is not None  # the fixture is only here to keep the intent readable


def test_a_none_scope_is_refused():
    """The final `return False`: a scope with no rule must not fall through to delivery."""
    none_scope = _ctx(data_scope=DataScope.NONE)
    assert not can_deliver_envelope(none_scope, _envelope(owner_id=str(uuid4())), resource_owner_id=uuid4())


def test_subscribed_channels_are_filtered_to_the_allowed_set():
    ctx = _ctx(permissions=frozenset({"business:quote:read"}))
    requested = ["notification", "quote", "workflow", "audit", "not-a-channel"]
    assert filter_subscribed_channels(requested, ctx) == ["quote", "workflow"], (
        filter_subscribed_channels(requested, ctx)
    )
    assert ctx.allowed_channels == frozenset({"quote", "workflow"})
