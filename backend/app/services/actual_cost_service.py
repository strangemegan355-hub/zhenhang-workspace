from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import scope_predicate, scope_predicate_via_parent
from app.models.project import Project
from app.models.project_actual_cost import ProjectActualCost
from app.models.user import User
from app.repositories import project_actual_cost_repository as repo
from app.repositories import project_repository as project_repo
from app.schemas.common import PageResponse
from app.schemas.common import page_response as _page
from app.schemas.project_actual_cost import ProjectActualCostCreate, ProjectActualCostRead

T = TypeVar("T", bound=BaseModel)

async def create_actual_cost(db: AsyncSession, payload: ProjectActualCostCreate, current_user: User) -> ProjectActualCostRead:
    # A write needs the same check as a read: nobody adds a cost to a project they cannot see.
    project = await project_repo.get_project(
        db, payload.project_id, predicate=scope_predicate(Project, current_user)
    )
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
    current_user: User,
    *,
    project_id: UUID | None = None,
) -> PageResponse:
    # Visibility follows the project, so a cost line is visible exactly when its project is.
    total, items = await repo.list_actual_costs(
        db,
        page,
        page_size,
        q,
        project_id=project_id,
        predicate=scope_predicate_via_parent(
            ProjectActualCost, Project, ProjectActualCost.project_id, current_user
        ),
    )
    return _page(total, page, page_size, items, ProjectActualCostRead)

async def get_actual_cost_or_404(
    db: AsyncSession, object_id: UUID, current_user: User
) -> ProjectActualCostRead:
    obj = await repo.get_actual_cost(
        db,
        object_id,
        predicate=scope_predicate_via_parent(
            ProjectActualCost, Project, ProjectActualCost.project_id, current_user
        ),
    )
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual cost entry not found")
    return ProjectActualCostRead.model_validate(obj)

async def delete_actual_cost(
    db: AsyncSession, object_id: UUID, current_user: User
) -> ProjectActualCostRead:
    obj = await repo.get_actual_cost(
        db,
        object_id,
        predicate=scope_predicate_via_parent(
            ProjectActualCost, Project, ProjectActualCost.project_id, current_user
        ),
    )
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Actual cost entry not found")
    deleted = await repo.soft_delete_actual_cost(db, obj)
    return ProjectActualCostRead.model_validate(deleted)
