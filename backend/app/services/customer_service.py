from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories import customer_repository as repo
from app.schemas.common import PageResponse


def _page(total: int, page: int, page_size: int, items: list) -> PageResponse:
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


async def create_customer(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_customer(db, payload)


async def list_customers(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_customers(db, page, page_size, q)
    return _page(total, page, page_size, items)


async def get_customer_or_404(db: AsyncSession, object_id):
    obj = await repo.get_customer(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return obj


async def update_customer(db: AsyncSession, object_id, payload: dict):
    obj = await get_customer_or_404(db, object_id)
    return await repo.update_customer(db, obj, payload)


async def delete_customer(db: AsyncSession, object_id):
    obj = await get_customer_or_404(db, object_id)
    return await repo.soft_delete_customer(db, obj)


async def create_customer_contact(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_customer_contact(db, payload)


async def list_customer_contacts(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_customer_contacts(db, page, page_size, q)
    return _page(total, page, page_size, items)


async def get_customer_contact_or_404(db: AsyncSession, object_id):
    obj = await repo.get_customer_contact(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer contact not found")
    return obj


async def update_customer_contact(db: AsyncSession, object_id, payload: dict):
    obj = await get_customer_contact_or_404(db, object_id)
    return await repo.update_customer_contact(db, obj, payload)


async def delete_customer_contact(db: AsyncSession, object_id):
    obj = await get_customer_contact_or_404(db, object_id)
    return await repo.soft_delete_customer_contact(db, obj)


async def create_customer_followup(db: AsyncSession, payload: dict, current_user: User):
    payload["created_by"] = current_user.id
    return await repo.create_customer_followup(db, payload)


async def list_customer_followups(db: AsyncSession, page: int, page_size: int, q: str | None) -> PageResponse:
    total, items = await repo.list_customer_followups(db, page, page_size, q)
    return _page(total, page, page_size, items)


async def get_customer_followup_or_404(db: AsyncSession, object_id):
    obj = await repo.get_customer_followup(db, object_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer followup not found")
    return obj


async def update_customer_followup(db: AsyncSession, object_id, payload: dict):
    obj = await get_customer_followup_or_404(db, object_id)
    return await repo.update_customer_followup(db, obj, payload)


async def delete_customer_followup(db: AsyncSession, object_id):
    obj = await get_customer_followup_or_404(db, object_id)
    return await repo.soft_delete_customer_followup(db, obj)
