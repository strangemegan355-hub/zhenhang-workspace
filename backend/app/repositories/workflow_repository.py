from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowState, WorkflowTransition
from app.repositories.common_repository import paginate_query


async def create_state(db: AsyncSession, data: dict, *, autocommit: bool = True) -> WorkflowState:
    obj = WorkflowState(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def create_transition(db: AsyncSession, data: dict, *, autocommit: bool = True) -> WorkflowTransition:
    obj = WorkflowTransition(**data)
    db.add(obj)
    await db.flush()
    if autocommit:
        await db.commit()
    await db.refresh(obj)
    return obj


async def page_states(db: AsyncSession, page: int, page_size: int, q: str | None, entity_type: str | None = None):
    extra = []
    if entity_type:
        extra.append(WorkflowState.entity_type == entity_type)
    return await paginate_query(
        db,
        WorkflowState,
        page,
        page_size,
        q,
        [WorkflowState.entity_type, WorkflowState.code, WorkflowState.name],
        extra,
    )


async def page_transitions(db: AsyncSession, page: int, page_size: int, q: str | None, entity_type: str | None = None):
    extra = []
    if entity_type:
        extra.append(WorkflowTransition.entity_type == entity_type)
    return await paginate_query(
        db,
        WorkflowTransition,
        page,
        page_size,
        q,
        [WorkflowTransition.entity_type, WorkflowTransition.action_code, WorkflowTransition.action_name],
        extra,
    )


async def get_state_by_code(db: AsyncSession, entity_type: str, code: str) -> WorkflowState | None:
    stmt = select(WorkflowState).where(
        WorkflowState.entity_type == entity_type,
        WorkflowState.code == code,
        WorkflowState.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_transition(
    db: AsyncSession,
    entity_type: str,
    from_state_id: UUID,
    action_code: str,
) -> WorkflowTransition | None:
    stmt = select(WorkflowTransition).where(
        WorkflowTransition.entity_type == entity_type,
        WorkflowTransition.from_state_id == from_state_id,
        WorkflowTransition.action_code == action_code,
        WorkflowTransition.is_deleted.is_(False),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_transitions_from_state(
    db: AsyncSession,
    entity_type: str,
    from_state_id: UUID,
) -> list[WorkflowTransition]:
    stmt = select(WorkflowTransition).where(
        WorkflowTransition.entity_type == entity_type,
        WorkflowTransition.from_state_id == from_state_id,
        WorkflowTransition.is_deleted.is_(False),
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_states(db: AsyncSession, entity_type: str) -> list[WorkflowState]:
    stmt = select(WorkflowState).where(
        WorkflowState.entity_type == entity_type,
        WorkflowState.is_deleted.is_(False),
    )
    return list((await db.execute(stmt)).scalars().all())
