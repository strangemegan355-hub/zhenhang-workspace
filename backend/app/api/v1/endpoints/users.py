from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import resolve_data_scope
from app.core.deps import get_current_active_user, require_permissions
from app.core.rbac import collect_permission_codes
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.user import UserAdminRead, UserCreate, UserPublic, UserRoleUpdate, UserUpdate
from app.services import admin_service as svc

router = APIRouter()

# Static paths are declared before "/{user_id}" on purpose: FastAPI matches in declaration
# order, so a dynamic segment registered first would swallow "/me" and "/rbac-demo".


@router.get("/me", response_model=UserPublic, summary="Current user profile")
async def read_me(
    current: Annotated[User, Depends(get_current_active_user)],
) -> UserPublic:
    permissions = sorted(collect_permission_codes(current))
    if current.is_superuser and "*:*:*" not in permissions:
        permissions.append("*:*:*")
    return UserPublic(
        id=current.id,
        username=current.username,
        email=current.email,
        full_name=current.full_name,
        phone=current.phone,
        is_active=current.is_active,
        is_superuser=current.is_superuser,
        department_id=current.department_id,
        roles=current.roles,
        permissions=permissions,
        data_scope=str(resolve_data_scope(current)),
    )


@router.get(
    "/rbac-demo",
    summary="Example RBAC-protected endpoint",
)
async def rbac_demo(
    _: Annotated[User, Depends(require_permissions("system:user:read"))],
) -> dict[str, bool]:
    return {"allowed": True}


@router.get("", response_model=PageResponse, summary="List users")
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:user:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
    department_id: UUID | None = Query(default=None),
) -> PageResponse:
    return await svc.list_users(db, page, page_size, q, department_id, current)


@router.post("", response_model=UserAdminRead, status_code=status.HTTP_201_CREATED, summary="Create user")
async def create_user(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:user:create"))],
) -> UserAdminRead:
    return await svc.create_user(db, payload.model_dump(), current)


@router.get("/{user_id}", response_model=UserAdminRead, summary="Get user")
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:user:read"))],
) -> UserAdminRead:
    return await svc.get_user_or_404(db, user_id, current)


@router.put("/{user_id}", response_model=UserAdminRead, summary="Update user")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:user:update"))],
) -> UserAdminRead:
    return await svc.update_user(db, user_id, payload.model_dump(exclude_unset=True), current)


@router.put("/{user_id}/roles", response_model=UserAdminRead, summary="Replace the roles of a user")
async def set_user_roles(
    user_id: UUID,
    payload: UserRoleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:user:assign"))],
) -> UserAdminRead:
    return await svc.set_user_roles(db, user_id, payload.role_codes, current)
