from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.aftersales import (
    AfterSalesServiceRequestCreate,
    AfterSalesServiceRequestRead,
    AfterSalesServiceRequestUpdate,
)
from app.schemas.common import PageResponse
from app.services import aftersales_service as svc

router = APIRouter()


@router.get("", response_model=PageResponse)
async def list_aftersales_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:aftersales:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    customer_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None, max_length=32),
    priority: str | None = Query(default=None, max_length=16),
    assigned_to: UUID | None = Query(default=None),
) -> PageResponse:
    return await svc.list_requests(
        db, page=page, page_size=page_size,
        customer_id=customer_id, status=status,
        priority=priority, assigned_to=assigned_to,
    )


@router.get("/{request_id}", response_model=AfterSalesServiceRequestRead)
async def get_aftersales_request(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:aftersales:read"))],
) -> AfterSalesServiceRequestRead:
    return await svc.get_request(db, request_id)


@router.post("", response_model=AfterSalesServiceRequestRead, status_code=status.HTTP_201_CREATED)
async def create_aftersales_request(
    payload: AfterSalesServiceRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:aftersales:create"))],
) -> AfterSalesServiceRequestRead:
    return await svc.create_request(db, payload, current)


@router.put("/{request_id}", response_model=AfterSalesServiceRequestRead)
async def update_aftersales_request(
    request_id: UUID,
    payload: AfterSalesServiceRequestUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:aftersales:update"))],
) -> AfterSalesServiceRequestRead:
    return await svc.update_request(db, request_id, payload)


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_aftersales_request(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:aftersales:delete"))],
) -> None:
    await svc.delete_request(db, request_id)
