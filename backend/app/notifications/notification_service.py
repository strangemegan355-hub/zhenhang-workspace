from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.realtime.publish import push_notification_event


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
        await push_notification_event(
            user_id=receiver_id,
            notification_id=obj.id,
            title=title,
            biz_type=biz_type,
            biz_id=biz_id,
        )
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
