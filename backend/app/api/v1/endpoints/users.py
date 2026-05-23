from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_active_user, require_permissions
from app.models.user import User
from app.schemas.user import UserPublic

router = APIRouter()


@router.get("/me", response_model=UserPublic, summary="Current user profile")
async def read_me(
    current: Annotated[User, Depends(get_current_active_user)],
) -> User:
    return current


@router.get(
    "/rbac-demo",
    summary="Example RBAC-protected endpoint",
)
async def rbac_demo(
    _: Annotated[User, Depends(require_permissions("system:user:read"))],
) -> dict[str, bool]:
    return {"allowed": True}
