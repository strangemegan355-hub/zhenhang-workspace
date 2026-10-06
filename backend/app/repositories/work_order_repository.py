from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.work_order import WorkOrder
from app.repositories.common_repository import get_by_id, paginate_query


async def count_work_order_no_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(WorkOrder).where(
        WorkOrder.work_order_no.like(f"{prefix}%"),
        WorkOrder.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def generate_work_order_no(db: AsyncSession) -> str:
    prefix = f"WO-{date.today().strftime('%Y%m%d')}-"
    count = await count_work_order_no_prefix(db, prefix)
    return f"{prefix}{count + 1:03d}"


async def create_work_order(db: AsyncSession, data: dict) -> WorkOrder:
    obj = WorkOrder(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_work_orders(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    *,
    project_id: UUID | None = None,
    status: str | None = None,
    predicate=None,
):
    extra_filters = []
    if predicate is not None:
        extra_filters.append(predicate)
    if project_id is not None:
        extra_filters.append(WorkOrder.project_id == project_id)
    if status:
        extra_filters.append(WorkOrder.status == status)
    return await paginate_query(
        db,
        WorkOrder,
        page,
        page_size,
        q,
        [WorkOrder.work_order_no, WorkOrder.task_desc, WorkOrder.team, WorkOrder.owner_name, WorkOrder.remark],
        extra_filters=extra_filters,
    )


async def get_work_order(db: AsyncSession, object_id: UUID, predicate=None) -> WorkOrder | None:
    return await get_by_id(db, WorkOrder, object_id, predicate)


async def update_work_order(db: AsyncSession, obj: WorkOrder, data: dict) -> WorkOrder:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_work_order(db: AsyncSession, obj: WorkOrder) -> WorkOrder:
    obj.is_deleted = True
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def count_by_status(db: AsyncSession, predicate=None) -> dict[str, int]:
    stmt = (
        select(WorkOrder.status, func.count())
        .where(WorkOrder.is_deleted.is_(False))
        .group_by(WorkOrder.status)
    )
    if predicate is not None:
        stmt = stmt.where(predicate)
    rows = (await db.execute(stmt)).all()
    return {status: int(count) for status, count in rows}


async def count_exceptions(db: AsyncSession, predicate=None) -> int:
    stmt = select(func.count()).select_from(WorkOrder).where(
        WorkOrder.is_deleted.is_(False),
        WorkOrder.exception_type.isnot(None),
        WorkOrder.exception_type != "",
        WorkOrder.status != "done",
    )
    if predicate is not None:
        stmt = stmt.where(predicate)
    return int((await db.execute(stmt)).scalar_one())


async def count_completed_today(db: AsyncSession, today: date, predicate=None) -> int:
    stmt = select(func.count()).select_from(WorkOrder).where(
        WorkOrder.is_deleted.is_(False),
        WorkOrder.status == "done",
        func.date(WorkOrder.actual_end) == today,
    )
    if predicate is not None:
        stmt = stmt.where(predicate)
    return int((await db.execute(stmt)).scalar_one())


async def list_kanban(
    db: AsyncSession, limit_per_column: int = 20, predicate=None
) -> dict[str, list[WorkOrder]]:
    result: dict[str, list[WorkOrder]] = {"todo": [], "doing": [], "done": []}
    scope = [predicate] if predicate is not None else []
    for status, key in (("todo", "todo"), ("doing", "doing"), ("qacheck", "doing"), ("done", "done")):
        if status == "qacheck":
            continue
        stmt = (
            select(WorkOrder)
            .where(WorkOrder.is_deleted.is_(False), WorkOrder.status == status, *scope)
            .order_by(WorkOrder.plan_end.asc().nullslast(), WorkOrder.updated_at.desc())
            .limit(limit_per_column)
        )
        items = list((await db.execute(stmt)).scalars().all())
        if status == "doing":
            qacheck_stmt = (
                select(WorkOrder)
                .where(WorkOrder.is_deleted.is_(False), WorkOrder.status == "qacheck", *scope)
                .order_by(WorkOrder.plan_end.asc().nullslast(), WorkOrder.updated_at.desc())
                .limit(limit_per_column)
            )
            items.extend(list((await db.execute(qacheck_stmt)).scalars().all()))
            items.sort(key=lambda x: (x.plan_end or date.max, x.updated_at), reverse=False)
            result[key] = items[:limit_per_column]
        else:
            result[key] = items
    return result
