from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.machine import MachineBom, MachineBomItem
from app.models.quote import (
    ApprovalNode,
    ApprovalRecord,
    ApprovalTemplate,
    Quote,
    QuoteApproval,
    QuoteExportTask,
    QuoteItem,
    QuoteVersion,
)


async def next_quote_sequence(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(Quote).where(Quote.quote_no.like(f"{prefix}%"))
    return int((await db.execute(stmt)).scalar_one()) + 1


async def create_quote(db: AsyncSession, data: dict, *, autocommit: bool = True) -> Quote:
    obj = Quote(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_quote_version(db: AsyncSession, data: dict, *, autocommit: bool = True) -> QuoteVersion:
    obj = QuoteVersion(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_quote_item(db: AsyncSession, data: dict, *, autocommit: bool = True) -> QuoteItem:
    obj = QuoteItem(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_quote_approval(db: AsyncSession, data: dict, *, autocommit: bool = True) -> QuoteApproval:
    obj = QuoteApproval(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_approval_record(db: AsyncSession, data: dict, *, autocommit: bool = True) -> ApprovalRecord:
    obj = ApprovalRecord(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def count_approval_records(db: AsyncSession, *, quote_id: UUID, node_id: UUID, action: str) -> int:
    stmt = select(func.count()).select_from(ApprovalRecord).where(
        ApprovalRecord.quote_id == quote_id,
        ApprovalRecord.node_id == node_id,
        ApprovalRecord.action == action,
        ApprovalRecord.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def create_approval_template(db: AsyncSession, data: dict, *, autocommit: bool = True) -> ApprovalTemplate:
    obj = ApprovalTemplate(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_approval_node(db: AsyncSession, data: dict, *, autocommit: bool = True) -> ApprovalNode:
    obj = ApprovalNode(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_export_task(db: AsyncSession, data: dict, *, autocommit: bool = True) -> QuoteExportTask:
    obj = QuoteExportTask(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def get_quote(db: AsyncSession, quote_id: UUID, predicate=None) -> Quote | None:
    """Fetch one quote, optionally restricted by a data-scope predicate.

    Taking the predicate here means an out-of-scope row is simply absent, so the caller can
    answer 404 instead of 403 and never confirms that the quote exists.
    """
    stmt = select(Quote).where(Quote.id == quote_id, Quote.is_deleted.is_(False))
    if predicate is not None:
        stmt = stmt.where(predicate)
    return (await db.execute(stmt)).scalar_one_or_none()


async def soft_delete_quote(db: AsyncSession, quote: Quote, *, autocommit: bool = True) -> Quote:
    quote.is_deleted = True
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(quote)
    return quote


async def update_quote(db: AsyncSession, quote: Quote, data: dict, *, autocommit: bool = True) -> Quote:
    for key, value in data.items():
        setattr(quote, key, value)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(quote)
    return quote


async def get_generic_machine_id(db: AsyncSession) -> UUID | None:
    from app.models.machine import Machine

    stmt = select(Machine.id).where(Machine.code == "GENERIC", Machine.is_deleted.is_(False)).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()


async def next_customer_quote_sequence(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(Quote).where(Quote.quote_no.like(f"{prefix}%"))
    return int((await db.execute(stmt)).scalar_one()) + 1


async def list_quotes(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    q: str | None,
    created_by: UUID | None = None,
    predicate=None,
    quote_kind: str | None = None,
):
    filters = [Quote.is_deleted.is_(False)]
    if created_by is not None:
        filters.append(Quote.created_by == created_by)
    if predicate is not None:
        filters.append(predicate)
    if quote_kind:
        filters.append(Quote.quote_kind == quote_kind)
    if q:
        key = f"%{q.strip()}%"
        filters.append(or_(cast(Quote.quote_no, String).ilike(key), cast(Quote.title, String).ilike(key)))
    count_stmt = select(func.count()).select_from(Quote).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())
    stmt = select(Quote).where(*filters).order_by(Quote.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    items = list((await db.execute(stmt)).scalars().all())
    return total, items


async def max_quote_version_no(db: AsyncSession, quote_id: UUID) -> int:
    stmt = select(func.max(QuoteVersion.version_no)).where(QuoteVersion.quote_id == quote_id, QuoteVersion.is_deleted.is_(False))
    value = (await db.execute(stmt)).scalar_one()
    return int(value or 0)


async def mark_other_versions_not_current(db: AsyncSession, quote_id: UUID) -> None:
    stmt = select(QuoteVersion).where(
        QuoteVersion.quote_id == quote_id,
        QuoteVersion.is_deleted.is_(False),
        QuoteVersion.is_current.is_(True),
    )
    items = (await db.execute(stmt)).scalars().all()
    for item in items:
        item.is_current = False
    await db.flush()


async def list_bom_items(db: AsyncSession, bom_id: UUID) -> list[MachineBomItem]:
    stmt = select(MachineBomItem).where(MachineBomItem.bom_id == bom_id, MachineBomItem.is_deleted.is_(False))
    return list((await db.execute(stmt)).scalars().all())


async def get_bom(db: AsyncSession, bom_id: UUID) -> MachineBom | None:
    stmt = select(MachineBom).where(MachineBom.id == bom_id, MachineBom.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_quote_state(db: AsyncSession, quote: Quote, new_state: str) -> Quote:
    quote.workflow_state = new_state
    await db.flush()
    await db.refresh(quote)
    return quote


async def get_quote_version_by_no(db: AsyncSession, quote_id: UUID, version_no: int) -> QuoteVersion | None:
    stmt = select(QuoteVersion).where(
        QuoteVersion.quote_id == quote_id,
        QuoteVersion.version_no == version_no,
        QuoteVersion.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_approval_template(db: AsyncSession, template_id: UUID) -> ApprovalTemplate | None:
    stmt = select(ApprovalTemplate).where(ApprovalTemplate.id == template_id, ApprovalTemplate.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_approval_templates(db: AsyncSession, *, page: int, page_size: int, q: str | None):
    filters = [ApprovalTemplate.is_deleted.is_(False)]
    if q:
        like_key = f"%{q.strip()}%"
        filters.append(or_(cast(ApprovalTemplate.code, String).ilike(like_key), cast(ApprovalTemplate.name, String).ilike(like_key)))
    count_stmt = select(func.count()).select_from(ApprovalTemplate).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())
    stmt = (
        select(ApprovalTemplate)
        .where(*filters)
        .order_by(ApprovalTemplate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return total, items


async def list_approval_nodes(db: AsyncSession, template_id: UUID) -> list[ApprovalNode]:
    stmt = select(ApprovalNode).where(
        ApprovalNode.template_id == template_id,
        ApprovalNode.is_deleted.is_(False),
    ).order_by(ApprovalNode.node_order.asc())
    return list((await db.execute(stmt)).scalars().all())


async def list_quote_items_by_version(db: AsyncSession, quote_version_id: UUID) -> list[QuoteItem]:
    stmt = select(QuoteItem).where(
        QuoteItem.quote_version_id == quote_version_id,
        QuoteItem.is_deleted.is_(False),
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_quote_item(db: AsyncSession, item_id: UUID) -> QuoteItem | None:
    stmt = select(QuoteItem).where(QuoteItem.id == item_id, QuoteItem.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_export_task(
    db: AsyncSession,
    task: QuoteExportTask,
    *,
    status: str,
    file_id: UUID | None = None,
    error_message: str | None = None,
    autocommit: bool = True,
) -> QuoteExportTask:
    task.status = status
    task.file_id = file_id
    task.error_message = error_message
    if status == "completed":
        task.completed_at = datetime.now(UTC)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(task)
    return task


async def get_export_task(db: AsyncSession, task_id: UUID) -> QuoteExportTask | None:
    stmt = select(QuoteExportTask).where(QuoteExportTask.id == task_id, QuoteExportTask.is_deleted.is_(False))
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_quote_versions(db: AsyncSession, quote_id: UUID) -> list[QuoteVersion]:
    stmt = (
        select(QuoteVersion)
        .where(QuoteVersion.quote_id == quote_id, QuoteVersion.is_deleted.is_(False))
        .order_by(QuoteVersion.version_no.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_current_quote_version(db: AsyncSession, quote_id: UUID) -> QuoteVersion | None:
    stmt = select(QuoteVersion).where(
        QuoteVersion.quote_id == quote_id,
        QuoteVersion.is_current.is_(True),
        QuoteVersion.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_quote_approvals(db: AsyncSession, quote_id: UUID) -> list[QuoteApproval]:
    stmt = (
        select(QuoteApproval)
        .where(QuoteApproval.quote_id == quote_id, QuoteApproval.is_deleted.is_(False))
        .order_by(QuoteApproval.acted_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())
