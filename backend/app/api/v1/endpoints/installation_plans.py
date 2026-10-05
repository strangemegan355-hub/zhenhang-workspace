from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.installation_plan import (
    InstallationPlanCreate,
    InstallationPlanRead,
    InstallationPlanUpdate,
)
from app.services import installation_plan_service as svc

router = APIRouter()


@router.get(
    "/equipment-units/{equipment_unit_id}/installation-plans",
    response_model=list[InstallationPlanRead],
)
async def list_plans(
    equipment_unit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> list[dict]:
    return await svc.list_plans(db, equipment_unit_id)


@router.post(
    "/equipment-units/{equipment_unit_id}/installation-plans",
    response_model=InstallationPlanRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    equipment_unit_id: UUID,
    payload: InstallationPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    data = payload.model_dump(by_alias=True)
    data["equipment_unit_id"] = equipment_unit_id
    return await svc.create_plan(db, data, current)


@router.get("/installation-plans/{plan_id}", response_model=InstallationPlanRead)
async def get_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> dict:
    try:
        return await svc.get_plan(db, plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/installation-plans/{plan_id}", response_model=InstallationPlanRead)
async def update_plan(
    plan_id: UUID,
    payload: InstallationPlanUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.update_plan(db, plan_id, payload.model_dump(exclude_unset=True, by_alias=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/installation-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> None:
    try:
        await svc.delete_plan(db, plan_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
