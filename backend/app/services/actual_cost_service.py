from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import project_actual_cost_repository as repo
from app.repositories import project_repository as project_repo
from app.schemas.common import PageResponse
from app.schemas.project_actual_cost import ProjectActualCostCreate, ProjectActualCostRead

T = TypeVar("T", bound=BaseModel)


def _page(total: int, page: int, page_size: int, items: list, schema: type[T]) -> PageResponse:
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[schema.model_validate(i) for i in items],
    )


async def create_actual_cost(db: AsyncSession, payload: ProjectActualCostCreate, current_user: User) -> ProjectActualCostRead:
    project = await project_repo.get_project(db, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    data = payload.model_dump()
    data["created_by"] = current_user.id
    obj = await repo.create_actual_cost(db, data)
    return ProjectActualCostRead.model_validate(obj)


async def list_actual_costs(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
    *,
    project_id: UUID | None = None,
) -> PageResponse:
    total, items = await repo.list_actual_costs(db, page, page_size, q, project_id=project_id)
    return _page(total, page, page_size, items, ProjectActualCostRead)


async def get_actual_cost_or_404(db: AsyncSession, object_id: UUID) -> ProjectActualCostRead:
    obj = await repo.get_actual_cost(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual cost entry not found")
    return ProjectActualCostRead.model_validate(obj)


async def delete_actual_cost(db: AsyncSession, object_id: UUID) -> ProjectActualCostRead:
    obj = await repo.get_actual_cost(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual cost entry not found")
    deleted = await repo.soft_delete_actual_cost(db, obj)
    return ProjectActualCostRead.model_validate(deleted)
