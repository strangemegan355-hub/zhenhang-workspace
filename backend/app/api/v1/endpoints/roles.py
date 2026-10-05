from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import RoleCreate, RolePermissionUpdate, RoleRead, RoleUpdate
from app.schemas.common import PageResponse
from app.services import admin_service as svc

router = APIRouter()


@router.get("", response_model=PageResponse, summary="List roles")
async def list_roles(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("system:role:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_roles(db, page, page_size, q)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED, summary="Create role")
async def create_role(
    payload: RoleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:role:create"))],
) -> RoleRead:
    return await svc.create_role(db, payload.model_dump(), current)


@router.get("/{role_id}", response_model=RoleRead, summary="Get role")
async def get_role(
    role_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("system:role:read"))],
) -> RoleRead:
    return await svc.get_role_or_404(db, role_id)


@router.put("/{role_id}", response_model=RoleRead, summary="Update role")
async def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:role:update"))],
) -> RoleRead:
    return await svc.update_role(db, role_id, payload.model_dump(exclude_unset=True), current)


@router.put(
    "/{role_id}/permissions",
    response_model=RoleRead,
    summary="Replace the permission set of a role",
)
async def set_role_permissions(
    role_id: UUID,
    payload: RolePermissionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:role:assign"))],
) -> RoleRead:
    return await svc.set_role_permissions(db, role_id, payload.permission_codes, current)
