from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import material_category_repository as repo
from app.schemas.common import PageResponse
from app.schemas.common import page_response as _page
from app.schemas.material_category import MaterialCategoryRead

T = TypeVar("T", bound=BaseModel)

async def create_material_category(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    obj = await repo.create_material_category(db, payload)
    return MaterialCategoryRead.model_validate(obj)

async def list_material_categories(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_material_categories(db, page, page_size, q)
    return _page(total, page, page_size, items, MaterialCategoryRead)

async def get_material_category_or_404(db: AsyncSession, object_id):
    obj = await repo.get_material_category(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material category not found")
    return MaterialCategoryRead.model_validate(obj)

async def update_material_category(db: AsyncSession, object_id, payload: dict):
    obj = await repo.get_material_category(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material category not found")
    updated = await repo.update_material_category(db, obj, payload)
    return MaterialCategoryRead.model_validate(updated)

async def delete_material_category(db: AsyncSession, object_id):
    obj = await repo.get_material_category(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material category not found")
    deleted = await repo.soft_delete_material_category(db, obj)
    return MaterialCategoryRead.model_validate(deleted)
