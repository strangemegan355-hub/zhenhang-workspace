from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import unit_repository as repo
from app.schemas.common import PageResponse
from app.schemas.common import page_response as _page
from app.schemas.unit import UnitRead

T = TypeVar("T", bound=BaseModel)

async def create_unit(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_unit(db, payload)
    return UnitRead.model_validate(obj)

async def list_units(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_units(db, page, page_size, q)
    return _page(total, page, page_size, items, UnitRead)

async def get_unit_or_404(db: AsyncSession, object_id):
    obj = await repo.get_unit(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    return UnitRead.model_validate(obj)

async def update_unit(db: AsyncSession, object_id, payload: dict):
    obj = await repo.get_unit(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    updated = await repo.update_unit(db, obj, payload)
    return UnitRead.model_validate(updated)

async def delete_unit(db: AsyncSession, object_id):
    obj = await repo.get_unit(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    deleted = await repo.soft_delete_unit(db, obj)
    return UnitRead.model_validate(deleted)
