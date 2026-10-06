from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import DataScope, resolve_data_scope
from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.notifications import notification_service as notify_svc
from app.schemas.common import PageResponse
from app.schemas.notification import NotificationRead, NotificationUnreadCount
from app.schemas.common import page_response

router = APIRouter()


@router.get("", response_model=PageResponse)
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:notification:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    status: str | None = Query(default=None, max_length=32),
    unread_only: bool = Query(default=False),
) -> PageResponse:
    filters = [Notification.is_deleted.is_(False)]
    if status:
        filters.append(Notification.status == status)
    if unread_only:
        filters.append(Notification.read_at.is_(None))
    if resolve_data_scope(current) != DataScope.ALL:
        filters.append(Notification.receiver_id == current.id)
    if q:
        key = f"%{q.strip()}%"
        filters.append(or_(cast(Notification.title, String).ilike(key), cast(Notification.content, String).ilike(key)))
    total = int((await db.execute(select(func.count()).select_from(Notification).where(*filters))).scalar_one())
    stmt = (
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return page_response(
        total=total,
        page=page,
        page_size=page_size,
        items=[NotificationRead.model_validate(i) for i in items],
    )


@router.get("/unread-count", response_model=NotificationUnreadCount)
async def unread_count(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:notification:read"))],
) -> NotificationUnreadCount:
    count = await notify_svc.count_unread_notifications(db, current.id)
    return NotificationUnreadCount(unread=count)


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:notification:read"))],
) -> NotificationRead:
    return await notify_svc.mark_notification_read(db, notification_id, current.id)
