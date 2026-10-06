from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import supplier_repository as repo
from app.schemas.common import PageResponse
from app.schemas.supplier import SupplierRead
from app.schemas.common import page_response as _page

T = TypeVar("T", bound=BaseModel)

async def create_supplier(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_supplier(db, payload)
    return SupplierRead.model_validate(obj)

async def list_suppliers(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_suppliers(db, page, page_size, q)
    return _page(total, page, page_size, items, SupplierRead)

async def get_supplier_or_404(db: AsyncSession, object_id):
    obj = await repo.get_supplier(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    return SupplierRead.model_validate(obj)

async def update_supplier(db: AsyncSession, object_id, payload: dict):
    obj = await repo.get_supplier(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    updated = await repo.update_supplier(db, obj, payload)
    return SupplierRead.model_validate(updated)

async def delete_supplier(db: AsyncSession, object_id):
    obj = await repo.get_supplier(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
    deleted = await repo.soft_delete_supplier(db, obj)
    return SupplierRead.model_validate(deleted)
