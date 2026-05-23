from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def create_audit_log(db: AsyncSession, data: dict, *, autocommit: bool = True) -> AuditLog:
    obj = AuditLog(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def query_audit_logs(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    q: str | None,
    module: str | None,
    action: str | None,
    resource_type: str | None,
    base_filter: object | None = None,
) -> tuple[int, list[AuditLog]]:
    filters = [AuditLog.is_deleted.is_(False)]
    if base_filter is not None:
        filters.append(base_filter)
    if module:
        filters.append(AuditLog.module == module)
    if action:
        filters.append(AuditLog.action == action)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if q:
        key = f"%{q.strip()}%"
        filters.append(
            or_(
                cast(AuditLog.module, String).ilike(key),
                cast(AuditLog.action, String).ilike(key),
                cast(AuditLog.resource_type, String).ilike(key),
                cast(AuditLog.detail, String).ilike(key),
            )
        )

    count_stmt = select(func.count()).select_from(AuditLog).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())
    stmt = (
        select(AuditLog)
        .where(*filters)
        .order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list((await db.execute(stmt)).scalars().all())
    return total, items
