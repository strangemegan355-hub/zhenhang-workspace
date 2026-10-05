from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.data_scope import resolve_data_scope
from app.core.deps import get_current_active_user, require_permissions
from app.core.rbac import collect_permission_codes
from app.models.user import User
from app.schemas.user import UserPublic

router = APIRouter()


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
