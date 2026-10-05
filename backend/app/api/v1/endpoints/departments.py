from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services import admin_service as svc

router = APIRouter()


@router.get("", response_model=list[DepartmentRead], summary="List departments as a flat tree")
async def list_departments(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("system:department:read"))],
) -> list[DepartmentRead]:
    """Flat list carrying parent_id, ordered by sort_order then code.

    The organisation is small and bounded, so it is returned whole rather than paginated: a
    paginated tree would hand clients a partial parent chain they cannot render.
    """
    return await svc.list_departments(db)


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create department",
)
async def create_department(
    payload: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:department:create"))],
) -> DepartmentRead:
    return await svc.create_department(db, payload.model_dump(), current)


@router.put("/{department_id}", response_model=DepartmentRead, summary="Update department")
async def update_department(
    department_id: UUID,
    payload: DepartmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("system:department:update"))],
) -> DepartmentRead:
    return await svc.update_department(db, department_id, payload.model_dump(exclude_unset=True), current)
