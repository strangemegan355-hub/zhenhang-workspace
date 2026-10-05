from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceRecordCreate,
    AcceptanceRecordRead,
    AcceptanceRecordUpdate,
    AcceptanceTemplateCreate,
    AcceptanceTemplateRead,
    AcceptanceTemplateUpdate,
    PunchListItemCreate,
    PunchListItemRead,
    PunchListItemUpdate,
)
from app.services import acceptance_service as svc

router = APIRouter()


# ── Templates ──

@router.get("/machines/{machine_id}/acceptance-templates", response_model=list[AcceptanceTemplateRead])
async def list_templates(
    machine_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> list[dict]:
    return await svc.list_templates(db, machine_id)


@router.post(
    "/machines/{machine_id}/acceptance-templates",
    response_model=AcceptanceTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    machine_id: UUID,
    payload: AcceptanceTemplateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    data = payload.model_dump()
    data["machine_id"] = machine_id
    return await svc.create_template(db, data, current)


@router.get("/acceptance-templates/{template_id}", response_model=AcceptanceTemplateRead)
async def get_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> dict:
    try:
        return await svc.get_template(db, template_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/acceptance-templates/{template_id}", response_model=AcceptanceTemplateRead)
async def update_template(
    template_id: UUID,
    payload: AcceptanceTemplateUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.update_template(db, template_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/acceptance-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> None:
    try:
        await svc.delete_template(db, template_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Records ──

@router.get(
    "/equipment-units/{equipment_unit_id}/acceptance-records",
    response_model=list[AcceptanceRecordRead],
)
async def list_records(
    equipment_unit_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> list[dict]:
    return await svc.list_records(db, equipment_unit_id)


@router.post(
    "/equipment-units/{equipment_unit_id}/acceptance-records",
    response_model=AcceptanceRecordRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_record(
    equipment_unit_id: UUID,
    payload: AcceptanceRecordCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    data = payload.model_dump(by_alias=True)
    data["equipment_unit_id"] = equipment_unit_id
    return await svc.create_record(db, data, current)


@router.get("/acceptance-records/{record_id}", response_model=AcceptanceRecordRead)
async def get_record(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
) -> dict:
    try:
        return await svc.get_record(db, record_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/acceptance-records/{record_id}", response_model=AcceptanceRecordRead)
async def update_record(
    record_id: UUID,
    payload: AcceptanceRecordUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.update_record(db, record_id, payload.model_dump(exclude_unset=True, by_alias=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/acceptance-records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> None:
    try:
        await svc.delete_record(db, record_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ── Punch items ──

@router.post(
    "/acceptance-records/{record_id}/punch-items",
    response_model=PunchListItemRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_punch_item(
    record_id: UUID,
    payload: PunchListItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.create_punch_item(db, record_id, payload.model_dump(), current)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/punch-items/{item_id}", response_model=PunchListItemRead)
async def update_punch_item(
    item_id: UUID,
    payload: PunchListItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> dict:
    try:
        return await svc.update_punch_item(db, item_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/punch-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_punch_item(
    item_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> None:
    try:
        await svc.delete_punch_item(db, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
