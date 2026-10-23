from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessException, UniqueViolationException
from app.models.user import User
from app.repositories import workflow_repository as repo
from app.schemas.common import page_response as _page
from app.schemas.workflow import WorkflowStateRead, WorkflowTransitionRead


async def create_state(db: AsyncSession, payload: dict, current_user: User):
    exists = await repo.get_state_by_code(db, payload["entity_type"], payload["code"])
    if exists is not None:
        raise UniqueViolationException("workflow_state.code", payload["code"])
    payload["created_by"] = current_user.id
    return await repo.create_state(db, payload)


async def create_transition(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_transition(db, payload)


async def list_states(db: AsyncSession, page: int, page_size: int, q: str | None, entity_type: str | None):
    total, items = await repo.page_states(db, page, page_size, q, entity_type)
    return _page(total, page, page_size, items, WorkflowStateRead)


async def list_transitions(db: AsyncSession, page: int, page_size: int, q: str | None, entity_type: str | None):
    total, items = await repo.page_transitions(db, page, page_size, q, entity_type)
    return _page(total, page, page_size, items, WorkflowTransitionRead)


async def seed_default_workflows(db: AsyncSession, current_user: User | None = None) -> dict[str, int]:
    created_state_count = 0
    created_transition_count = 0
    seed_plans = [
        (
            "machine_bom",
            [
                {"code": "draft", "name": "草稿", "is_start": True, "is_end": False},
                {"code": "reviewing", "name": "审核中", "is_start": False, "is_end": False},
                {"code": "approved", "name": "已生效", "is_start": False, "is_end": True},
                {"code": "rejected", "name": "已驳回", "is_start": False, "is_end": False},
            ],
            [
                ("draft", "reviewing", "submit", "提交审核"),
                ("reviewing", "approved", "approve", "审核通过"),
                ("reviewing", "rejected", "reject", "审核驳回"),
                ("rejected", "draft", "resubmit", "重新提交"),
            ],
        ),
        (
            "quote",
            [
                {"code": "draft", "name": "草稿", "is_start": True, "is_end": False},
                {"code": "reviewing", "name": "待审批", "is_start": False, "is_end": False},
                {"code": "approved", "name": "已审批", "is_start": False, "is_end": True},
                {"code": "rejected", "name": "已拒绝", "is_start": False, "is_end": True},
            ],
            [
                ("draft", "reviewing", "submit", "提交审批"),
                ("reviewing", "approved", "approve", "审批通过"),
                ("reviewing", "rejected", "reject", "审批拒绝"),
            ],
        ),
    ]

    async with db.begin():
        for entity_type, state_defs, transition_defs in seed_plans:
            for state_def in state_defs:
                existing = await repo.get_state_by_code(db, entity_type, state_def["code"])
                if existing is not None:
                    continue
                await repo.create_state(
                    db,
                    {
                        "entity_type": entity_type,
                        "code": state_def["code"],
                        "name": state_def["name"],
                        "is_start": state_def["is_start"],
                        "is_end": state_def["is_end"],
                        "created_by": getattr(current_user, "id", None),
                    },
                    autocommit=False,
                )
                created_state_count += 1

            for from_code, to_code, action_code, action_name in transition_defs:
                from_state = await repo.get_state_by_code(db, entity_type, from_code)
                to_state = await repo.get_state_by_code(db, entity_type, to_code)
                if from_state is None or to_state is None:
                    continue
                existing = await repo.get_transition(db, entity_type, from_state.id, action_code)
                if existing is not None:
                    continue
                await repo.create_transition(
                    db,
                    {
                        "entity_type": entity_type,
                        "from_state_id": from_state.id,
                        "to_state_id": to_state.id,
                        "action_code": action_code,
                        "action_name": action_name,
                        "created_by": getattr(current_user, "id", None),
                    },
                    autocommit=False,
                )
                created_transition_count += 1

    return {"states_created": created_state_count, "transitions_created": created_transition_count}


async def list_available_actions(db: AsyncSession, *, entity_type: str, current_state_code: str) -> list[dict]:
    current = await repo.get_state_by_code(db, entity_type, current_state_code)
    if current is None:
        return []
    transitions = await repo.list_transitions_from_state(db, entity_type, current.id)
    states = {s.id: s for s in await repo.list_states(db, entity_type)}
    actions = []
    for tr in transitions:
        to_state = states.get(tr.to_state_id)
        actions.append(
            {
                "action_code": tr.action_code,
                "action_name": tr.action_name,
                "from_state": current_state_code,
                "to_state": to_state.code if to_state else None,
            }
        )
    return actions


async def get_next_state_code(
    db: AsyncSession,
    *,
    entity_type: str,
    current_state_code: str,
    action_code: str,
) -> str:
    current = await repo.get_state_by_code(db, entity_type, current_state_code)
    if current is None:
        raise BusinessException("WORKFLOW_STATE_NOT_FOUND", f"State '{current_state_code}' not found", status_code=404)

    transition = await repo.get_transition(db, entity_type, current.id, action_code)
    if transition is None:
        raise BusinessException(
            "WORKFLOW_TRANSITION_INVALID",
            f"Action '{action_code}' is not allowed from '{current_state_code}'",
            status_code=400,
        )
    states = {s.id: s for s in await repo.list_states(db, entity_type)}
    to_state = states.get(transition.to_state_id)
    if to_state is None:
        raise BusinessException("WORKFLOW_STATE_NOT_FOUND", "Target workflow state not found", status_code=404)
    return to_state.code
