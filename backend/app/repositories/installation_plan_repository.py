from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.installation_plan import InstallationPlan


async def list_plans(db: AsyncSession, equipment_unit_id: UUID) -> list[InstallationPlan]:
    stmt = (
        select(InstallationPlan)
        .where(
            InstallationPlan.equipment_unit_id == equipment_unit_id,
            InstallationPlan.is_deleted == False,
        )
        .order_by(InstallationPlan.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_plan_by_id(db: AsyncSession, plan_id: UUID) -> InstallationPlan | None:
    stmt = select(InstallationPlan).where(
        InstallationPlan.id == plan_id, InstallationPlan.is_deleted == False
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_plan(db: AsyncSession, data: dict, user_id: UUID) -> InstallationPlan:
    p = InstallationPlan(created_by=user_id, is_deleted=False, **data)
    db.add(p)
    await db.flush()
    await db.commit()
    return p


async def update_plan(db: AsyncSession, plan: InstallationPlan, data: dict) -> InstallationPlan:
    for key, value in data.items():
        if value is not None:
            setattr(plan, key, value)
    await db.flush()
    await db.commit()
    return plan


async def delete_plan(db: AsyncSession, plan: InstallationPlan) -> None:
    plan.is_deleted = True
    await db.flush()
    await db.commit()
