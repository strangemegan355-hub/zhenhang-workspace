from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate
from app.models.user import User
from app.models.work_order import WorkOrder
from app.repositories import project_repository as project_repo
from app.repositories import work_order_repository as repo
from app.schemas.common import PageResponse
from app.schemas.work_order import (
    WorkOrderChainResult,
    WorkOrderClaim,
    WorkOrderCreate,
    WorkOrderGenerateChain,
    WorkOrderRead,
    WorkOrderSummary,
    WorkOrderUpdate,
)

_PROCESS_NODE_LABELS = {
    "cutting": "下料",
    "welding": "焊装",
    "assembly": "装配",
    "debug": "调试",
    "shipment": "发货",
}

_STATUS_LABELS = {
    "todo": "待认领",
    "doing": "进行中",
    "qacheck": "待质检",
    "done": "已完成",
}

_STATUS_FLOW = ("todo", "doing", "done")

_STANDARD_CHAIN = (
    ("cutting", "下料班组", "下料负责人"),
    ("welding", "焊装班组", "焊装负责人"),
    ("assembly", "装配班组", "装配负责人"),
    ("debug", "调试班组", "调试负责人"),
    ("shipment", "发货班组", "储运负责人"),
)


def _node_label(node: str) -> str:
    return _PROCESS_NODE_LABELS.get(node, node)


def _status_label(status: str) -> str:
    if status == "qacheck":
        return _STATUS_LABELS["doing"]
    return _STATUS_LABELS.get(status, status)


def _to_read(obj) -> WorkOrderRead:
    return WorkOrderRead(
        id=obj.id,
        work_order_no=obj.work_order_no,
        project_id=obj.project_id,
        machine_id=obj.machine_id,
        task_desc=obj.task_desc,
        process_node=obj.process_node,
        process_node_label=_node_label(obj.process_node),
        team=obj.team,
        owner_name=obj.owner_name,
        claimed_by=obj.claimed_by,
        status=obj.status,
        status_label=_status_label(obj.status),
        plan_start=obj.plan_start,
        plan_end=obj.plan_end,
        actual_start=obj.actual_start,
        actual_end=obj.actual_end,
        actual_hours=float(obj.actual_hours or 0),
        drawing_version=obj.drawing_version,
        exception_type=obj.exception_type,
        remark=obj.remark,
        created_at=obj.created_at,
        updated_at=obj.updated_at,
        created_by=obj.created_by,
        is_deleted=obj.is_deleted,
    )


async def _ensure_project(db: AsyncSession, project_id: UUID):
    project = await project_repo.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _maybe_set_manufacturing(db: AsyncSession, project_id: UUID) -> None:
    project = await project_repo.get_project(db, project_id)
    if project and project.stage != "manufacturing":
        project.stage = "manufacturing"
        await db.flush()


async def create_work_order(db: AsyncSession, payload: WorkOrderCreate, current_user: User) -> WorkOrderRead:
    await _ensure_project(db, payload.project_id)
    data = payload.model_dump()
    if not data.get("work_order_no"):
        data["work_order_no"] = await repo.generate_work_order_no(db)
    data["created_by"] = current_user.id
    obj = await repo.create_work_order(db, data)
    return _to_read(obj)


async def list_work_orders(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    current_user: User,
    *,
    project_id: UUID | None = None,
    status: str | None = None,
) -> PageResponse:
    total, items = await repo.list_work_orders(
        db,
        page,
        page_size,
        q,
        project_id=project_id,
        status=status,
        predicate=scope_predicate(WorkOrder, current_user),
    )
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_read(i) for i in items],
    )


async def get_work_order_or_404(
    db: AsyncSession, object_id: UUID, current_user: User
) -> WorkOrderRead:
    obj = await repo.get_work_order(db, object_id, predicate=scope_predicate(WorkOrder, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    return _to_read(obj)


async def update_work_order(
    db: AsyncSession, object_id: UUID, payload: WorkOrderUpdate, current_user: User
) -> WorkOrderRead:
    obj = await repo.get_work_order(db, object_id, predicate=scope_predicate(WorkOrder, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    if obj.status == "done":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Completed work orders cannot be edited")
    updated = await repo.update_work_order(db, obj, payload.model_dump(exclude_unset=True))
    return _to_read(updated)


async def delete_work_order(
    db: AsyncSession, object_id: UUID, current_user: User
) -> WorkOrderRead:
    obj = await repo.get_work_order(db, object_id, predicate=scope_predicate(WorkOrder, current_user))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    deleted = await repo.soft_delete_work_order(db, obj)
    return _to_read(deleted)


async def advance_work_order_status(db: AsyncSession, object_id: UUID) -> WorkOrderRead:
    obj = await repo.get_work_order(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    status_value = "doing" if obj.status == "qacheck" else obj.status
    try:
        idx = _STATUS_FLOW.index(status_value)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid work order status") from None
    if idx >= len(_STATUS_FLOW) - 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Work order already completed")
    now = datetime.now(UTC)
    obj.status = _STATUS_FLOW[idx + 1]
    if obj.status == "doing" and obj.actual_start is None:
        obj.actual_start = now
        await _maybe_set_manufacturing(db, obj.project_id)
    if obj.status == "done":
        obj.actual_end = now
        if not obj.actual_hours:
            obj.actual_hours = 1
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return _to_read(obj)


async def claim_work_order(db: AsyncSession, object_id: UUID, payload: WorkOrderClaim) -> WorkOrderRead:
    obj = await repo.get_work_order(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")
    if obj.status not in ("todo", "qacheck"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Work order cannot be claimed")
    now = datetime.now(UTC)
    obj.status = "doing"
    obj.claimed_by = payload.claimed_by
    if obj.actual_start is None:
        obj.actual_start = now
    await _maybe_set_manufacturing(db, obj.project_id)
    await db.flush()
    await db.commit()
    await db.refresh(obj)
    return _to_read(obj)


async def generate_standard_chain(
    db: AsyncSession,
    payload: WorkOrderGenerateChain,
    current_user: User,
) -> WorkOrderChainResult:
    await _ensure_project(db, payload.project_id)
    start = payload.start_date or date.today()
    step_days = payload.step_days
    cursor = start
    created: list[WorkOrderRead] = []
    for node, team, owner in _STANDARD_CHAIN:
        plan_start = cursor
        plan_end = cursor + timedelta(days=step_days - 1)
        obj = await repo.create_work_order(
            db,
            {
                "work_order_no": await repo.generate_work_order_no(db),
                "project_id": payload.project_id,
                "task_desc": f"{_node_label(node)}（标准工序链）",
                "process_node": node,
                "team": team,
                "owner_name": owner,
                "status": "todo",
                "plan_start": plan_start,
                "plan_end": plan_end,
                "drawing_version": payload.drawing_version,
                "remark": "标准工序链自动生成",
                "created_by": current_user.id,
            },
        )
        created.append(_to_read(obj))
        cursor = plan_end + timedelta(days=1)
    await _maybe_set_manufacturing(db, payload.project_id)
    await db.commit()
    return WorkOrderChainResult(created_count=len(created), items=created)


async def get_summary(db: AsyncSession) -> WorkOrderSummary:
    counts = await repo.count_by_status(db)
    todo = counts.get("todo", 0)
    doing = counts.get("doing", 0) + counts.get("qacheck", 0)
    done = counts.get("done", 0)
    total = todo + doing + done
    return WorkOrderSummary(
        total=total,
        todo=todo,
        doing=doing,
        done=done,
        exception_count=await repo.count_exceptions(db),
        completed_today=await repo.count_completed_today(db, date.today()),
    )


def serialize_for_board(obj) -> dict:
    read = _to_read(obj)
    project = getattr(obj, "project", None)
    machine = getattr(obj, "machine", None)
    return {
        "id": str(read.id),
        "work_order_no": read.work_order_no,
        "project_id": str(read.project_id),
        "project_no": project.project_no if project else None,
        "project_name": project.name if project else None,
        "machine_id": str(read.machine_id) if read.machine_id else None,
        "machine_name": machine.name if machine else None,
        "task_desc": read.task_desc,
        "process_node": read.process_node,
        "process_node_label": read.process_node_label,
        "team": read.team,
        "owner_name": read.owner_name,
        "claimed_by": read.claimed_by,
        "status": read.status,
        "status_label": read.status_label,
        "plan_end": read.plan_end.isoformat() if read.plan_end else None,
        "exception_type": read.exception_type,
    }
