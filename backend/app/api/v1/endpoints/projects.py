from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.project import (
    ProjectCreate,
    ProjectProfitLedgerResponse,
    ProjectRead,
    ProjectSummaryRead,
    ProjectUpdate,
)
from app.services import project_service as svc

router = APIRouter()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:create"))],
) -> ProjectRead:
    return await svc.create_project(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse)
async def list_projects(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_projects(db, page, page_size, q, current)


@router.get("/profit-ledger", response_model=ProjectProfitLedgerResponse)
async def list_profit_ledger(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    over_budget_only: bool = Query(default=False),
) -> ProjectProfitLedgerResponse:
    return await svc.list_profit_ledger(
        db, page, page_size, q, current, over_budget_only=over_budget_only
    )


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:read"))],
) -> ProjectRead:
    return await svc.get_project_or_404(db, project_id, current)


@router.get("/{project_id}/summary", response_model=ProjectSummaryRead)
async def get_project_summary(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:read"))],
) -> ProjectSummaryRead:
    return await svc.get_project_summary(db, project_id, current)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:update"))],
) -> ProjectRead:
    return await svc.update_project(db, project_id, payload.model_dump(exclude_unset=True), current)


@router.delete("/{project_id}", response_model=ProjectRead)
async def delete_project(
    project_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:project:delete"))],
) -> ProjectRead:
    return await svc.delete_project(db, project_id, current)
