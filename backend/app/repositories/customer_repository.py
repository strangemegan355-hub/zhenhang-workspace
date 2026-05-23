from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerContact, CustomerFollowup
from app.repositories.common_repository import get_by_id, paginate_query


async def create_customer(db: AsyncSession, data: dict) -> Customer:
    obj = Customer(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_customers(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[int, list[Customer]]:
    return await paginate_query(db, Customer, page, page_size, q, [Customer.code, Customer.name, Customer.phone])


async def get_customer(db: AsyncSession, object_id: UUID) -> Customer | None:
    return await get_by_id(db, Customer, object_id)


async def update_customer(db: AsyncSession, obj: Customer, data: dict) -> Customer:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_customer(db: AsyncSession, obj: Customer) -> Customer:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj


async def create_customer_contact(db: AsyncSession, data: dict) -> CustomerContact:
    obj = CustomerContact(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_customer_contacts(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[int, list[CustomerContact]]:
    return await paginate_query(
        db,
        CustomerContact,
        page,
        page_size,
        q,
        [CustomerContact.name, CustomerContact.phone, CustomerContact.email],
    )


async def get_customer_contact(db: AsyncSession, object_id: UUID) -> CustomerContact | None:
    return await get_by_id(db, CustomerContact, object_id)


async def update_customer_contact(db: AsyncSession, obj: CustomerContact, data: dict) -> CustomerContact:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_customer_contact(db: AsyncSession, obj: CustomerContact) -> CustomerContact:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj


async def create_customer_followup(db: AsyncSession, data: dict) -> CustomerFollowup:
    obj = CustomerFollowup(**data)
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


async def list_customer_followups(
    db: AsyncSession,
    page: int,
    page_size: int,
    q: str | None,
) -> tuple[int, list[CustomerFollowup]]:
    return await paginate_query(
        db,
        CustomerFollowup,
        page,
        page_size,
        q,
        [CustomerFollowup.followup_type, CustomerFollowup.content],
    )


async def get_customer_followup(db: AsyncSession, object_id: UUID) -> CustomerFollowup | None:
    return await get_by_id(db, CustomerFollowup, object_id)


async def update_customer_followup(db: AsyncSession, obj: CustomerFollowup, data: dict) -> CustomerFollowup:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.commit()
    await db.refresh(obj)
    return obj


async def soft_delete_customer_followup(db: AsyncSession, obj: CustomerFollowup) -> CustomerFollowup:
    obj.is_deleted = True
    await db.commit()
    await db.refresh(obj)
    return obj
