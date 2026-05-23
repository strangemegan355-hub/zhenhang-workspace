from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.core.data_scope import DataScope, resolve_data_scope
from app.core.rbac import collect_permission_codes
from app.models.user import User

CHANNEL_PERMISSIONS: dict[str, str] = {
    "notification": "platform:notification:read",
    "workflow": "business:quote:read",
    "quote": "business:quote:read",
    "audit": "dashboard:view",
}

WORKSHOP_ROLE_CODES = frozenset({"admin", "workshop", "production", "operator"})


@dataclass(frozen=True)
class RealtimeACLContext:
    user_id: UUID
    permissions: frozenset[str]
    data_scope: DataScope
    department_id: UUID | None
    tenant_id: UUID | None
    role_codes: frozenset[str]
    is_superuser: bool

    @property
    def allowed_channels(self) -> frozenset[str]:
        if self.is_superuser or "*:*:*" in self.permissions:
            return frozenset(CHANNEL_PERMISSIONS.keys())
        allowed: set[str] = set()
        for channel, perm in CHANNEL_PERMISSIONS.items():
            if perm in self.permissions:
                allowed.add(channel)
        if self.role_codes & WORKSHOP_ROLE_CODES:
            allowed.update({"quote", "workflow", "audit"})
        return frozenset(allowed)


def build_acl_context(user: User) -> RealtimeACLContext:
    perms = collect_permission_codes(user)
    roles = {str(r.code) for r in getattr(user, "roles", []) if getattr(r, "code", None)}
    return RealtimeACLContext(
        user_id=user.id,
        permissions=frozenset(perms),
        data_scope=resolve_data_scope(user),
        department_id=getattr(user, "department_id", None),
        tenant_id=getattr(user, "tenant_id", None),
        role_codes=frozenset(roles),
        is_superuser=bool(getattr(user, "is_superuser", False)),
    )


def _payload_owner_id(envelope: dict) -> UUID | None:
    payload = envelope.get("payload") or {}
    if not isinstance(payload, dict):
        return None
    for key in ("owner_id", "created_by", "actor_id", "receiver_id"):
        raw = payload.get(key)
        if raw:
            try:
                return UUID(str(raw))
            except (ValueError, TypeError):
                continue
    return None


def _record_visible_to_user(
    ctx: RealtimeACLContext,
    *,
    audience: str,
    audience_user_id: UUID | None,
    audience_department_id: UUID | None,
    resource_owner_id: UUID | None,
    envelope: dict,
) -> bool:
    if audience == "user":
        return audience_user_id == ctx.user_id
    if audience == "department":
        if ctx.data_scope == DataScope.ALL:
            return True
        return ctx.department_id is not None and audience_department_id == ctx.department_id
    owner = resource_owner_id or _payload_owner_id(envelope)
    if ctx.data_scope == DataScope.ALL:
        return True
    if ctx.data_scope == DataScope.SELF:
        if owner is None:
            return True
        return owner == ctx.user_id
    if ctx.data_scope == DataScope.DEPARTMENT:
        if owner is None:
            return True
        return ctx.department_id is not None
    return False


def can_deliver_envelope(
    ctx: RealtimeACLContext,
    envelope: dict,
    *,
    audience: str = "broadcast",
    audience_user_id: UUID | None = None,
    audience_department_id: UUID | None = None,
    resource_owner_id: UUID | None = None,
) -> bool:
    channel = str(envelope.get("channel", "notification"))
    if channel not in ctx.allowed_channels:
        return False
    msg_type = envelope.get("message_type", "event")
    if msg_type in {"heartbeat", "heartbeat_ack", "subscribe_ack"}:
        return True
    payload = envelope.get("payload") or {}
    if isinstance(payload, dict):
        kind = str(payload.get("kind", ""))
        if kind == "notification.new" and audience == "user":
            return audience_user_id == ctx.user_id
    return _record_visible_to_user(
        ctx,
        audience=audience,
        audience_user_id=audience_user_id,
        audience_department_id=audience_department_id,
        resource_owner_id=resource_owner_id,
        envelope=envelope,
    )


def filter_subscribed_channels(requested: list[str], ctx: RealtimeACLContext) -> list[str]:
    allowed = ctx.allowed_channels
    return [c for c in requested if c in allowed]
