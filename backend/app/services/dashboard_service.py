from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import DataScope, resolve_data_scope
from app.domains.quote.policies.data_scope_policy import owner_scope_user_id
from app.domains.quote.repositories import quote_repository as quote_repo
from app.models.notification import Notification
from app.models.quote import Quote, QuoteExportTask
from app.models.user import User


async def get_dashboard_overview(db: AsyncSession, current_user: User) -> dict:
    owner_id = owner_scope_user_id(current_user)
    quote_filters = [Quote.is_deleted.is_(False)]
    if owner_id is not None:
        quote_filters.append(Quote.created_by == owner_id)

    total_quotes = int(
        (await db.execute(select(func.count()).select_from(Quote).where(*quote_filters))).scalar_one()
    )
    reviewing = int(
        (
            await db.execute(
                select(func.count()).select_from(Quote).where(*quote_filters, Quote.workflow_state == "reviewing")
            )
        ).scalar_one()
    )
    approved = int(
        (
            await db.execute(
                select(func.count()).select_from(Quote).where(*quote_filters, Quote.workflow_state == "approved")
            )
        ).scalar_one()
    )
    draft = int(
        (
            await db.execute(
                select(func.count()).select_from(Quote).where(*quote_filters, Quote.workflow_state == "draft")
            )
        ).scalar_one()
    )

    amount_sum = (
        await db.execute(select(func.coalesce(func.sum(Quote.total_amount), 0)).where(*quote_filters))
    ).scalar_one()

    notif_filters = [Notification.is_deleted.is_(False), Notification.read_at.is_(None)]
    if resolve_data_scope(current_user) != DataScope.ALL:
        notif_filters.append(Notification.receiver_id == current_user.id)
    unread_notifications = int(
        (await db.execute(select(func.count()).select_from(Notification).where(*notif_filters))).scalar_one()
    )

    export_pending = int(
        (
            await db.execute(
                select(func.count()).select_from(QuoteExportTask).where(
                    QuoteExportTask.is_deleted.is_(False),
                    QuoteExportTask.status == "pending",
                )
            )
        ).scalar_one()
    )

    _, recent = await quote_repo.list_quotes(db, page=1, page_size=8, q=None, created_by=owner_id)
    recent_items = [
        {
            "id": str(q.id),
            "quote_no": q.quote_no,
            "title": q.title,
            "workflow_state": q.workflow_state,
            "total_amount": str(q.total_amount),
            "updated_at": q.updated_at.isoformat() if q.updated_at else None,
        }
        for q in recent
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "kpis": {
            "total_quotes": total_quotes,
            "pending_approval": reviewing,
            "approved_quotes": approved,
            "draft_quotes": draft,
            "quote_amount_total": str(amount_sum),
            "unread_notifications": unread_notifications,
            "export_pending": export_pending,
        },
        "recent_quotes": recent_items,
        "pipeline": [
            {"state": "draft", "count": draft},
            {"state": "reviewing", "count": reviewing},
            {"state": "approved", "count": approved},
        ],
    }
