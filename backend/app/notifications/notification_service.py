"""Create and read in-app notifications, and say plainly what that means.

Only the in-app channel is implemented. For it, the stored row *is* the delivery: the list endpoint
serves the notification to its receiver, so "sent" means "visible to its receiver in the app".
It does not mean emailed, texted or posted to a webhook — `NotificationProvider` models those
channels and no sender exists for them anywhere in the codebase, which is why no notification is
ever given a `provider_id`.

The realtime push below is a live-update convenience on top of the stored row, not the delivery.
It is therefore best-effort: a failure is logged and cannot fail the creation, because the
notification the receiver can already read must not be lost to a missed toast.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.realtime.publish import push_notification_event

logger = logging.getLogger(__name__)


async def create_notification(
    db: AsyncSession,
    *,
    title: str,
    content: str,
    biz_type: str,
    biz_id: UUID | None,
    receiver_id: UUID | None,
    payload: dict | None,
    created_by: UUID | None,
    autocommit: bool = False,
) -> Notification:
    obj = Notification(
        channel="inapp",
        title=title,
        content=content,
        biz_type=biz_type,
        biz_id=biz_id,
        receiver_id=receiver_id,
        status="sent",
        sent_at=datetime.now(UTC),
        payload=payload,
        created_by=created_by,
    )
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    if receiver_id is not None:
        try:
            await push_notification_event(
                user_id=receiver_id,
                notification_id=obj.id,
                title=title,
                biz_type=biz_type,
                biz_id=biz_id,
            )
        except Exception:  # noqa: BLE001 - a lost live update must not lose the notification
            logger.exception("notification %s could not be pushed to receiver %s", obj.id, receiver_id)
    return obj


async def mark_notification_read(db: AsyncSession, notification_id: UUID, receiver_id: UUID) -> Notification:
    stmt = select(Notification).where(
        Notification.id == notification_id,
        Notification.is_deleted.is_(False),
        Notification.receiver_id == receiver_id,
    )
    obj = (await db.execute(stmt)).scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    obj.status = "read"
    obj.read_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(obj)
    return obj


async def count_unread_notifications(db: AsyncSession, receiver_id: UUID) -> int:
    stmt = select(func.count()).select_from(Notification).where(
        Notification.is_deleted.is_(False),
        Notification.receiver_id == receiver_id,
        Notification.read_at.is_(None),
    )
    return int((await db.execute(stmt)).scalar_one())
