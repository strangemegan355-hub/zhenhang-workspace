from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import material_repository as repo
from app.schemas.common import PageResponse
from app.schemas.material import MaterialRead
from app.schemas.common import page_response as _page

T = TypeVar("T", bound=BaseModel)

async def create_material(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_material(db, payload)
    return MaterialRead.model_validate(obj)

async def list_materials(db: AsyncSession, page: int, page_size: int, q: str | None, category_id=None) -> PageResponse:
    total, items = await repo.list_materials(db, page, page_size, q, category_id)
    return _page(total, page, page_size, items, MaterialRead)

async def get_material_or_404(db: AsyncSession, object_id):
    obj = await repo.get_material(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    return MaterialRead.model_validate(obj)

async def update_material(db: AsyncSession, object_id, payload: dict):
    obj = await repo.get_material(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    updated = await repo.update_material(db, obj, payload)
    return MaterialRead.model_validate(updated)

async def delete_material(db: AsyncSession, object_id):
    obj = await repo.get_material(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found")
    deleted = await repo.soft_delete_material(db, obj)
    return MaterialRead.model_validate(deleted)
