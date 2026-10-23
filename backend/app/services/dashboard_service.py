from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import DataScope, resolve_data_scope
from app.domains.quote.public import queries as quote_repo
from app.domains.quote.public.queries import owner_scope_user_id
from app.models.notification import Notification
from app.models.quote import Quote, QuoteExportTask
from app.models.user import User
from app.services import project_service as project_svc


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

    # Export tasks belong to somebody too: the route for one is guarded, so the count must match what the
    # caller can open.
    export_filters = [QuoteExportTask.is_deleted.is_(False), QuoteExportTask.status == "pending"]
    if owner_id is not None:
        export_filters.append(QuoteExportTask.created_by == owner_id)
    export_pending = int(
        (await db.execute(select(func.count()).select_from(QuoteExportTask).where(*export_filters))).scalar_one()
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

    profit_agg = await project_svc.aggregate_profit_kpis(db, current_user)

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
        "profit_kpis": {
            "active_projects": profit_agg["active_projects"],
            "over_budget_count": profit_agg["over_budget_count"],
            "total_realized_profit": profit_agg["total_realized_profit"],
            "total_variance": profit_agg["total_variance"],
        },
        "over_budget_top3": profit_agg["over_budget_top3"],
        "recent_quotes": recent_items,
        "pipeline": [
            {"state": "draft", "count": draft},
            {"state": "reviewing", "count": reviewing},
            {"state": "approved", "count": approved},
        ],
    }
