from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_actual_cost import ProjectActualCost
from app.repositories.common_repository import get_by_id, paginate_query


async def create_actual_cost(db: AsyncSession, data: dict) -> ProjectActualCost:
    obj = ProjectActualCost(**data)
    db.add(obj)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_actual_costs(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    *,
    project_id: UUID | None = None,
):
    extra_filters = []
    if project_id is not None:
        extra_filters.append(ProjectActualCost.project_id == project_id)
    return await paginate_query(
        db,
        ProjectActualCost,
        page,
        page_size,
        q,
        [ProjectActualCost.cost_item_name, ProjectActualCost.source, ProjectActualCost.remark],
        extra_filters=extra_filters,
    )


async def get_actual_cost(db: AsyncSession, object_id: UUID) -> ProjectActualCost | None:
    return await get_by_id(db, ProjectActualCost, object_id)


async def find_by_procurement_ref(db: AsyncSession, procurement_ref: str) -> ProjectActualCost | None:
    stmt = select(ProjectActualCost).where(
        ProjectActualCost.procurement_ref == procurement_ref,
        ProjectActualCost.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def soft_delete_actual_cost(db: AsyncSession, obj: ProjectActualCost) -> ProjectActualCost:
    obj.is_deleted = True
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return obj


async def sum_amount_by_project(db: AsyncSession, project_id: UUID) -> tuple[int, float]:
    count_stmt = select(func.count()).select_from(ProjectActualCost).where(
        ProjectActualCost.project_id == project_id,
        ProjectActualCost.is_deleted.is_(False),
    )
    sum_stmt = select(func.coalesce(func.sum(ProjectActualCost.amount), 0)).where(
        ProjectActualCost.project_id == project_id,
        ProjectActualCost.is_deleted.is_(False),
    )
    count = int((await db.execute(count_stmt)).scalar_one())
    total = float((await db.execute(sum_stmt)).scalar_one())
    return count, total
