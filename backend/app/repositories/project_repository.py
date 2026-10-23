from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cost_estimate import CostEstimate
from app.models.project import Project
from app.models.quote import Quote, QuoteVersion
from app.repositories.common_repository import get_by_id, paginate_query


async def count_project_no_prefix(db: AsyncSession, prefix: str) -> int:
    stmt = select(func.count()).select_from(Project).where(
        Project.project_no.like(f"{prefix}%"),
        Project.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())


async def generate_project_no(db: AsyncSession) -> str:
    prefix = f"PRJ-{date.today().strftime('%Y%m%d')}-"
    count = await count_project_no_prefix(db, prefix)
    return f"{prefix}{count + 1:03d}"


async def create_project(db: AsyncSession, data: dict) -> Project:
    obj = Project(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_projects(
    db: AsyncSession, page: int, page_size: int, q: str | None, predicate=None
):
    """List projects, optionally restricted by a data-scope predicate.

    `paginate_query` accepts extra filters, so the scope lands in the same statement that counts
    and pages the rows instead of being applied to the page after the fact.
    """
    extra_filters = (predicate,) if predicate is not None else ()
    return await paginate_query(
        db,
        Project,
        page,
        page_size,
        q,
        [Project.project_no, Project.name, Project.category, Project.owner_name],
        extra_filters=extra_filters,
    )


async def get_project(db: AsyncSession, object_id: UUID, predicate=None) -> Project | None:
    """Fetch one project, optionally restricted by a data-scope predicate.

    With a predicate an out-of-scope project is simply absent, which lets the caller answer 404
    rather than confirming that the row exists.
    """
    if predicate is None:
        return await get_by_id(db, Project, object_id)
    stmt = select(Project).where(Project.id == object_id, Project.is_deleted.is_(False), predicate)
    return (await db.execute(stmt)).scalar_one_or_none()


async def update_project(db: AsyncSession, obj: Project, data: dict) -> Project:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_project(db: AsyncSession, obj: Project) -> Project:
    obj.is_deleted = True
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def get_quote_by_id(db: AsyncSession, quote_id: UUID, predicate=None) -> Quote | None:
    stmt = select(Quote).where(Quote.id == quote_id, Quote.is_deleted.is_(False))
    if predicate is not None:
        stmt = stmt.where(predicate)
    return (await db.execute(stmt)).scalar_one_or_none()


async def find_linked_quote(db: AsyncSession, project: Project) -> Quote | None:
    if project.primary_quote_id:
        found = await get_quote_by_id(db, project.primary_quote_id)
        if found:
            return found
    stmt = (
        select(Quote)
        .where(Quote.project_id == project.id, Quote.is_deleted.is_(False))
        .order_by(Quote.updated_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def find_current_quote_version(db: AsyncSession, quote_id: UUID) -> QuoteVersion | None:
    stmt = select(QuoteVersion).where(
        QuoteVersion.quote_id == quote_id,
        QuoteVersion.is_current.is_(True),
        QuoteVersion.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def find_linked_cost_estimate(db: AsyncSession, project_id: UUID) -> CostEstimate | None:
    stmt = (
        select(CostEstimate)
        .where(CostEstimate.project_id == project_id, CostEstimate.is_deleted.is_(False))
        .order_by(CostEstimate.updated_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def count_quotes_for_project(db: AsyncSession, project_id: UUID) -> int:
    stmt = select(func.count()).select_from(Quote).where(Quote.project_id == project_id, Quote.is_deleted.is_(False))
    return int((await db.execute(stmt)).scalar_one())


async def count_cost_estimates_for_project(db: AsyncSession, project_id: UUID) -> int:
    stmt = select(func.count()).select_from(CostEstimate).where(
        CostEstimate.project_id == project_id,
        CostEstimate.is_deleted.is_(False),
    )
    return int((await db.execute(stmt)).scalar_one())
