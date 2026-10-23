from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.customer import (
    CustomerContactCreate,
    CustomerContactRead,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerFollowupCreate,
    CustomerFollowupRead,
    CustomerFollowupUpdate,
    CustomerRead,
    CustomerUpdate,
)
from app.services import customer_service as svc

router = APIRouter()


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:customer:create"))],
) -> CustomerRead:
    return await svc.create_customer(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[CustomerRead])
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_customers(db, page, page_size, q)


@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer:update"))],
) -> CustomerRead:
    return await svc.update_customer(db, customer_id, payload.model_dump(exclude_unset=True))


@router.delete("/{customer_id}", response_model=CustomerRead)
async def delete_customer(
    customer_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer:delete"))],
) -> CustomerRead:
    return await svc.delete_customer(db, customer_id)


@router.post("/contacts", response_model=CustomerContactRead, status_code=status.HTTP_201_CREATED)
async def create_customer_contact(
    payload: CustomerContactCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:customer_contact:create"))],
) -> CustomerContactRead:
    return await svc.create_customer_contact(db, payload.model_dump(), current)


@router.get("/contacts", response_model=PageResponse[CustomerContactRead])
async def list_customer_contacts(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer_contact:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_customer_contacts(db, page, page_size, q)


@router.put("/contacts/{contact_id}", response_model=CustomerContactRead)
async def update_customer_contact(
    contact_id: UUID,
    payload: CustomerContactUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer_contact:update"))],
) -> CustomerContactRead:
    return await svc.update_customer_contact(db, contact_id, payload.model_dump(exclude_unset=True))


@router.delete("/contacts/{contact_id}", response_model=CustomerContactRead)
async def delete_customer_contact(
    contact_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer_contact:delete"))],
) -> CustomerContactRead:
    return await svc.delete_customer_contact(db, contact_id)


@router.post("/followups", response_model=CustomerFollowupRead, status_code=status.HTTP_201_CREATED)
async def create_customer_followup(
    payload: CustomerFollowupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("master:customer_followup:create"))],
) -> CustomerFollowupRead:
    return await svc.create_customer_followup(db, payload.model_dump(), current)


@router.get("/followups", response_model=PageResponse[CustomerFollowupRead])
async def list_customer_followups(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer_followup:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
) -> PageResponse:
    return await svc.list_customer_followups(db, page, page_size, q)


@router.put("/followups/{followup_id}", response_model=CustomerFollowupRead)
async def update_customer_followup(
    followup_id: UUID,
    payload: CustomerFollowupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer_followup:update"))],
) -> CustomerFollowupRead:
    return await svc.update_customer_followup(db, followup_id, payload.model_dump(exclude_unset=True))


@router.delete("/followups/{followup_id}", response_model=CustomerFollowupRead)
async def delete_customer_followup(
    followup_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("master:customer_followup:delete"))],
) -> CustomerFollowupRead:
    return await svc.delete_customer_followup(db, followup_id)
