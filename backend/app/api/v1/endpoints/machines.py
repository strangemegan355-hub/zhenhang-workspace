from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.machine import (
    MachineCategoryCreate,
    MachineCategoryRead,
    MachineCategoryUpdate,
    MachineCreate,
    MachineImageCreate,
    MachineImageRead,
    MachineImageUpdate,
    MachineParameterCreate,
    MachineParameterRead,
    MachineParameterUpdate,
    MachineRead,
    MachineUpdate,
)
from app.services import machine_service as svc

router = APIRouter()


@router.post("/categories", response_model=MachineCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_machine_category(
    payload: MachineCategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine_category:create"))],
) -> MachineCategoryRead:
    return await svc.create_machine_category(db, payload.model_dump(), current)


@router.get("/categories", response_model=PageResponse)
async def list_machine_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_category:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_machine_categories(db, page, page_size, q)


@router.put("/categories/{category_id}", response_model=MachineCategoryRead)
async def update_machine_category(
    category_id: UUID,
    payload: MachineCategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_category:update"))],
) -> MachineCategoryRead:
    return await svc.update_machine_category(db, category_id, payload.model_dump(exclude_unset=True))


@router.delete("/categories/{category_id}", response_model=MachineCategoryRead)
async def delete_machine_category(
    category_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_category:delete"))],
) -> MachineCategoryRead:
    return await svc.delete_machine_category(db, category_id)


@router.post("", response_model=MachineRead, status_code=status.HTTP_201_CREATED)
async def create_machine(
    payload: MachineCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine:create"))],
) -> MachineRead:
    return await svc.create_machine(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse)
async def list_machines(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_machines(db, page, page_size, q)


@router.put("/{machine_id}", response_model=MachineRead)
async def update_machine(
    machine_id: UUID,
    payload: MachineUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:update"))],
) -> MachineRead:
    return await svc.update_machine(db, machine_id, payload.model_dump(exclude_unset=True))


@router.delete("/{machine_id}", response_model=MachineRead)
async def delete_machine(
    machine_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine:delete"))],
) -> MachineRead:
    return await svc.delete_machine(db, machine_id)


@router.post("/parameters", response_model=MachineParameterRead, status_code=status.HTTP_201_CREATED)
async def create_machine_parameter(
    payload: MachineParameterCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine_parameter:create"))],
) -> MachineParameterRead:
    return await svc.create_machine_parameter(db, payload.model_dump(), current)


@router.get("/parameters", response_model=PageResponse)
async def list_machine_parameters(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_parameter:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_machine_parameters(db, page, page_size, q)


@router.put("/parameters/{parameter_id}", response_model=MachineParameterRead)
async def update_machine_parameter(
    parameter_id: UUID,
    payload: MachineParameterUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_parameter:update"))],
) -> MachineParameterRead:
    return await svc.update_machine_parameter(db, parameter_id, payload.model_dump(exclude_unset=True))


@router.delete("/parameters/{parameter_id}", response_model=MachineParameterRead)
async def delete_machine_parameter(
    parameter_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_parameter:delete"))],
) -> MachineParameterRead:
    return await svc.delete_machine_parameter(db, parameter_id)


@router.post("/images", response_model=MachineImageRead, status_code=status.HTTP_201_CREATED)
async def create_machine_image(
    payload: MachineImageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:machine_image:create"))],
) -> MachineImageRead:
    return await svc.create_machine_image(db, payload.model_dump(), current)


@router.get("/images", response_model=PageResponse)
async def list_machine_images(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_image:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_machine_images(db, page, page_size, q)


@router.put("/images/{image_id}", response_model=MachineImageRead)
async def update_machine_image(
    image_id: UUID,
    payload: MachineImageUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_image:update"))],
) -> MachineImageRead:
    return await svc.update_machine_image(db, image_id, payload.model_dump(exclude_unset=True))


@router.delete("/images/{image_id}", response_model=MachineImageRead)
async def delete_machine_image(
    image_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:machine_image:delete"))],
) -> MachineImageRead:
    return await svc.delete_machine_image(db, image_id)
