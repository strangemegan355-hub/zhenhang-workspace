from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.services.audit_service import write_audit_log


async def handle_quote_created(db: AsyncSession, payload: dict) -> None:
    resource_id = payload.get("quote_id")
    if resource_id is not None and not isinstance(resource_id, UUID):
        resource_id = UUID(str(resource_id))
    await write_audit_log(
        db,
        module="quote",
        action="domain_event.quote_created",
        resource_type="quote",
        resource_id=resource_id,
        created_by=payload.get("created_by"),
        payload=payload,
        autocommit=False,
    )
