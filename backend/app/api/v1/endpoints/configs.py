from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.domains.config.application import config_application_service as app_svc
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.config import SystemConfigCreate, SystemConfigRead, SystemConfigUpdate

router = APIRouter()


@router.post("", response_model=SystemConfigRead, status_code=status.HTTP_201_CREATED)
async def create_system_config(
    payload: SystemConfigCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:config:create"))],
) -> SystemConfigRead:
    return await app_svc.create_config(db, payload.model_dump(), current)


@router.put("/{config_id}", response_model=SystemConfigRead)
async def update_system_config(
    config_id: UUID,
    payload: SystemConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:config:update"))],
) -> SystemConfigRead:
    return await app_svc.update_config(db, config_id, payload.model_dump(exclude_unset=True), current)


@router.get("", response_model=PageResponse)
async def list_system_configs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:config:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    group: str | None = Query(default=None, max_length=64),
) -> PageResponse:
    return await app_svc.list_configs(db, page=page, page_size=page_size, q=q, group=group, current_user=current)
