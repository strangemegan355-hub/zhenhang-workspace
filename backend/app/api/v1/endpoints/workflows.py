from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.workflow import (
    WorkflowStateCreate,
    WorkflowStateRead,
    WorkflowTransitionCreate,
    WorkflowTransitionRead,
)
from app.services import workflow_service as svc

router = APIRouter()


@router.post("/states", response_model=WorkflowStateRead, status_code=status.HTTP_201_CREATED)
async def create_workflow_state(
    payload: WorkflowStateCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:workflow_state:create"))],
) -> WorkflowStateRead:
    return await svc.create_state(db, payload.model_dump(), current)


@router.get("/states", response_model=PageResponse[WorkflowStateRead])
async def list_workflow_states(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:workflow_state:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    entity_type: str | None = Query(default=None, max_length=64),
) -> PageResponse:
    return await svc.list_states(db, page, page_size, q, entity_type)


@router.post("/transitions", response_model=WorkflowTransitionRead, status_code=status.HTTP_201_CREATED)
async def create_workflow_transition(
    payload: WorkflowTransitionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:workflow_transition:create"))],
) -> WorkflowTransitionRead:
    return await svc.create_transition(db, payload.model_dump(), current)


@router.get("/transitions", response_model=PageResponse[WorkflowTransitionRead])
async def list_workflow_transitions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:workflow_transition:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    entity_type: str | None = Query(default=None, max_length=64),
) -> PageResponse:
    return await svc.list_transitions(db, page, page_size, q, entity_type)


@router.get("/actions")
async def list_workflow_actions(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:workflow_transition:read"))],
    entity_type: str = Query(..., max_length=64),
    current_state: str = Query(..., max_length=64),
) -> list[dict]:
    return await svc.list_available_actions(db, entity_type=entity_type, current_state_code=current_state)


@router.post("/seed", summary="Initialize default workflow seeds")
async def seed_default_workflows(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:workflow_state:create"))],
) -> dict:
    return await svc.seed_default_workflows(db, current_user=current)
