from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

# Round 227: every list route bounds `page_size` (`le=100` or `le=200`) and **none bounds `page`** — 42 route parameters,
# zero upper bounds — so `?page=100000000&page_size=100` asked the database for `OFFSET 9999999900`. The offset is what
# costs, and this is the one place all 42 of them flow through.
#
# The ceiling is on the OFFSET rather than on `page`, so it holds for any page size a route allows. **A page within the
# cap is untouched**, which is every page any client can reach by paging normally; a page beyond it clamps to the same
# offset instead of scanning.
MAX_OFFSET = 100_000


async def paginate_query(
    db: AsyncSession,
    model: Any,
    page: int,
    page_size: int,
    q: str | None = None,
    search_fields: Sequence[Any] = (),
    extra_filters: Sequence[Any] = (),
) -> tuple[int, list[Any]]:
    filters = [model.is_deleted.is_(False), *extra_filters]
    if q:
        keyword = f"%{q.strip()}%"
        search_conds = [cast(field, String).ilike(keyword) for field in search_fields]
        if search_conds:
            filters.append(or_(*search_conds))

    count_stmt = select(func.count()).select_from(model).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())

    stmt = (
        select(model)
        .where(*filters)
        .offset(min(max(page - 1, 0) * page_size, MAX_OFFSET))
        .limit(page_size)
        .order_by(model.created_at.desc())
    )
    items = list((await db.execute(stmt)).scalars().all())
    return total, items


async def get_by_id(db: AsyncSession, model: Any, object_id: UUID, predicate=None) -> Any | None:
    """Fetch one row by primary key, optionally restricted by a data-scope predicate.

    One implementation for every repository: a predicate makes an out-of-scope row simply absent,
    so the caller answers 404 without confirming that the row exists.
    """
    stmt = select(model).where(model.id == object_id, model.is_deleted.is_(False))
    if predicate is not None:
        stmt = stmt.where(predicate)
    return (await db.execute(stmt)).scalar_one_or_none()

