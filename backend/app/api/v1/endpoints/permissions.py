from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import PermissionRead
from app.schemas.common import PageResponse
from app.services import admin_service as svc

router = APIRouter()


@router.get("", response_model=PageResponse[PermissionRead], summary="List permission codes")
async def list_permissions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("system:permission:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    """The catalogue is read-only over the API.

    Permission rows are created by the seeding scripts so that a route can never be granted
    over HTTP without a code existing in source control first.
    """
    return await svc.list_permissions(db, page, page_size, q)
