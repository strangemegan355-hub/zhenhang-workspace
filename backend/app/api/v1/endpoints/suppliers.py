from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services import supplier_service as svc

router = APIRouter()


@router.post("", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
async def create_supplier(
    payload: SupplierCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:supplier:create"))],
) -> SupplierRead:
    return await svc.create_supplier(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse)
async def list_suppliers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:supplier:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_suppliers(db, page, page_size, q)


@router.get("/{supplier_id}", response_model=SupplierRead)
async def get_supplier(
    supplier_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:supplier:read"))],
) -> SupplierRead:
    return await svc.get_supplier_or_404(db, supplier_id)


@router.put("/{supplier_id}", response_model=SupplierRead)
async def update_supplier(
    supplier_id: UUID,
    payload: SupplierUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:supplier:update"))],
) -> SupplierRead:
    return await svc.update_supplier(db, supplier_id, payload.model_dump(exclude_unset=True))


@router.delete("/{supplier_id}", response_model=SupplierRead)
async def delete_supplier(
    supplier_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:supplier:delete"))],
) -> SupplierRead:
    return await svc.delete_supplier(db, supplier_id)
