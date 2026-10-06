from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import TenantCreate, TenantRead, TenantUpdate
from app.schemas.common import PageResponse
from app.services import admin_service as svc

router = APIRouter()


@router.get("", response_model=PageResponse[TenantRead], summary="List tenants")
async def list_tenants(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("system:tenant:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_tenants(db, page, page_size, q)


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED, summary="Create tenant")
async def create_tenant(
    payload: TenantCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:tenant:create"))],
) -> TenantRead:
    return await svc.create_tenant(db, payload.model_dump(), current)


@router.get("/{tenant_id}", response_model=TenantRead, summary="Get tenant")
async def get_tenant(
    tenant_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("system:tenant:read"))],
) -> TenantRead:
    return await svc.get_tenant_or_404(db, tenant_id)


@router.put("/{tenant_id}", response_model=TenantRead, summary="Update tenant")
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:tenant:update"))],
) -> TenantRead:
    return await svc.update_tenant(db, tenant_id, payload.model_dump(exclude_unset=True), current)
