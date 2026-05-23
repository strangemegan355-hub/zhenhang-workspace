from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.machine import (
    BatchIdsPayload,
    BatchMachineBomItemCreate,
    MachineBomCreate,
    MachineBomItemCreate,
    MachineBomItemRead,
    MachineBomItemUpdate,
    MachineBomRead,
    MachineBomUpdate,
)
from app.schemas.workflow import WorkflowActionPayload
from app.services import machine_service as svc

router = APIRouter()


@router.post("", response_model=MachineBomRead, status_code=status.HTTP_201_CREATED)
async def create_machine_bom(
    payload: MachineBomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:bom:create"))],
) -> MachineBomRead:
    return await svc.create_machine_bom(db, payload.model_dump(), current)


@router.get("/{bom_id}", response_model=MachineBomRead)
async def get_machine_bom(
    bom_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom:read"))],
) -> MachineBomRead:
    return await svc.get_machine_bom(db, bom_id)


@router.get("", response_model=PageResponse)
async def list_machine_boms(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_machine_boms(db, page, page_size, q)


@router.put("/{bom_id}", response_model=MachineBomRead)
async def update_machine_bom(
    bom_id: UUID,
    payload: MachineBomUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom:update"))],
) -> MachineBomRead:
    return await svc.update_machine_bom(db, bom_id, payload.model_dump(exclude_unset=True))


@router.delete("/{bom_id}", response_model=MachineBomRead)
async def delete_machine_bom(
    bom_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom:delete"))],
) -> MachineBomRead:
    return await svc.delete_machine_bom(db, bom_id)


@router.post("/items", response_model=MachineBomItemRead, status_code=status.HTTP_201_CREATED)
async def create_machine_bom_item(
    payload: MachineBomItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:bom_item:create"))],
) -> MachineBomItemRead:
    return await svc.create_machine_bom_item(db, payload.model_dump(), current)


@router.post("/items/batch", response_model=list[MachineBomItemRead], status_code=status.HTTP_201_CREATED)
async def create_machine_bom_items_batch(
    payload: BatchMachineBomItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:bom_item:create"))],
) -> list[MachineBomItemRead]:
    return await svc.create_bom_items_batch(db, [i.model_dump() for i in payload.items], current)


@router.get("/items", response_model=PageResponse)
async def list_machine_bom_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom_item:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    bom_id: UUID | None = Query(default=None),
) -> PageResponse:
    return await svc.list_machine_bom_items(db, page, page_size, q, bom_id=bom_id)


@router.put("/items/{item_id}", response_model=MachineBomItemRead)
async def update_machine_bom_item(
    item_id: UUID,
    payload: MachineBomItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom_item:update"))],
) -> MachineBomItemRead:
    return await svc.update_machine_bom_item(db, item_id, payload.model_dump(exclude_unset=True))


@router.delete("/items/{item_id}", response_model=MachineBomItemRead)
async def delete_machine_bom_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:bom_item:delete"))],
) -> MachineBomItemRead:
    return await svc.delete_machine_bom_item(db, item_id)


@router.post("/batch-delete")
async def delete_machine_boms_batch(
    payload: BatchIdsPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:bom:delete"))],
) -> dict:
    return await svc.delete_machine_boms_batch(db, payload.ids, current)


@router.post("/{bom_id}/actions/transition", response_model=MachineBomRead)
async def transition_machine_bom_status(
    bom_id: UUID,
    payload: WorkflowActionPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:bom:update"))],
) -> MachineBomRead:
    return await svc.transition_bom_status(db, bom_id, payload.action_code, current)
