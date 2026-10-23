from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.project_actual_cost import ProjectActualCostCreate, ProjectActualCostRead
from app.services import actual_cost_service as svc

router = APIRouter()


@router.post("", response_model=ProjectActualCostRead, status_code=status.HTTP_201_CREATED)
async def create_actual_cost(
    payload: ProjectActualCostCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:actual_cost:create"))],
) -> ProjectActualCostRead:
    return await svc.create_actual_cost(db, payload, current)


@router.get("", response_model=PageResponse[ProjectActualCostRead])
async def list_actual_costs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:actual_cost:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    project_id: UUID | None = Query(default=None),
) -> PageResponse:
    return await svc.list_actual_costs(
        db, page, page_size, q, current_user=current, project_id=project_id
    )


@router.get("/{entry_id}", response_model=ProjectActualCostRead)
async def get_actual_cost(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:actual_cost:read"))],
) -> ProjectActualCostRead:
    return await svc.get_actual_cost_or_404(db, entry_id, current_user=current)


@router.delete("/{entry_id}", response_model=ProjectActualCostRead)
async def delete_actual_cost(
    entry_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:actual_cost:delete"))],
) -> ProjectActualCostRead:
    return await svc.delete_actual_cost(db, entry_id, current_user=current)
