from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.option_group import (
    MachineOptionsRead,
    OptionGroupCreate,
    OptionGroupRead,
    OptionGroupUpdate,
    OptionItemCreate,
    OptionItemRead,
    OptionItemUpdate,
)
from app.services import option_group_service as svc

router = APIRouter()


@router.get(
    "/machines/{machine_id}/option-groups",
    response_model=list[OptionGroupRead],
)
async def list_option_groups(
    machine_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> list[dict]:
    return await svc.list_option_groups(db, machine_id)


@router.post(
    "/machines/{machine_id}/option-groups",
    response_model=OptionGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_option_group(
    machine_id: UUID,
    payload: OptionGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    return await svc.create_option_group(db, machine_id, payload.model_dump(), current)


@router.put("/option-groups/{group_id}", response_model=OptionGroupRead)
async def update_option_group(
    group_id: UUID,
    payload: OptionGroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.update_option_group(db, group_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/option-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option_group(
    group_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> None:
    try:
        await svc.delete_option_group(db, group_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/option-groups/{group_id}/items",
    response_model=OptionItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_option_item(
    group_id: UUID,
    payload: OptionItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.create_option_item(db, group_id, payload.model_dump(), current)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/option-items/{item_id}", response_model=OptionItemRead)
async def update_option_item(
    item_id: UUID,
    payload: OptionItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.update_option_item(db, item_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/option-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_option_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> None:
    try:
        await svc.delete_option_item(db, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/machines/{machine_id}/options",
    response_model=list[OptionGroupRead],
)
async def get_machine_options(
    machine_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> list[dict]:
    """Flat list of option groups with items, used by quote option selection panel."""
    return await svc.get_machine_options(db, machine_id)
