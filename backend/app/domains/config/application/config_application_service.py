from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UniqueViolationException
from app.domains.config.policies.data_scope_policy import owner_scope_user_id
from app.domains.config.repositories import config_repository as repo
from app.domains.events.application.event_bus import event_bus
from app.schemas.common import PageResponse
from app.services.audit_service import write_audit_log


async def create_config(db: AsyncSession, payload: dict, current_user):
    if await repo.get_config_by_key(db, payload["key"]) is not None:
        raise UniqueViolationException("system_config.key", payload["key"])
    payload["created_by"] = current_user.id
    obj = await repo.create_config(db, payload)
    await write_audit_log(
        db,
        module="config",
        action="create",
        resource_type="system_config",
        resource_id=obj.id,
        created_by=current_user.id,
        payload=payload,
        autocommit=False,
    )
    await event_bus.publish(
        db,
        event_type="system_config.created",
        aggregate_type="system_config",
        aggregate_id=obj.id,
        payload={"config_id": obj.id, "key": obj.key, "created_by": current_user.id},
        created_by=current_user.id,
    )
    await db.commit()
    return obj


async def update_config(db: AsyncSession, config_id, payload: dict, current_user):
    obj = await repo.get_config_by_id(db, config_id)
    # The domain's own owner convention, as list_configs applies it. 404 rather than 403, so a config outside
    # the caller's scope is indistinguishable from a missing one.
    owner_id = owner_scope_user_id(current_user)
    if obj is not None and owner_id is not None and obj.created_by != owner_id:
        obj = None
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System config not found")
    updated = await repo.update_config(db, obj, payload, autocommit=False)
    await write_audit_log(
        db,
        module="config",
        action="update",
        resource_type="system_config",
        resource_id=obj.id,
        created_by=current_user.id,
        payload=payload,
        autocommit=False,
    )
    await db.commit()
    await db.refresh(updated)
    return updated


async def list_configs(db: AsyncSession, *, page: int, page_size: int, q: str | None, group: str | None, current_user):
    owner_id = owner_scope_user_id(current_user)
    total, items = await repo.list_configs(
        db,
        page=page,
        page_size=page_size,
        q=q,
        group=group,
        created_by=owner_id,
    )
    return PageResponse(total=total, page=page, page_size=page_size, items=items)
