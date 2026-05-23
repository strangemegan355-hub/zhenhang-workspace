from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.data_scope import build_created_by_filter
from app.models.audit import AuditLog
from app.repositories.audit_repository import create_audit_log, query_audit_logs
from app.schemas.common import PageResponse


async def write_audit_log(
    db: AsyncSession,
    *,
    module: str,
    action: str,
    resource_type: str,
    resource_id: UUID | None,
    created_by: UUID | None,
    detail: str | None = None,
    payload: dict | None = None,
    autocommit: bool = False,
) -> None:
    await create_audit_log(
        db,
        {
            "module": module,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "detail": detail,
            "payload": payload,
            "created_by": created_by,
        },
        autocommit=autocommit,
    )


async def list_audit_logs(
    db: AsyncSession,
    *,
    page: int,
    page_size: int,
    q: str | None,
    module: str | None,
    action: str | None,
    resource_type: str | None,
    current_user,
) -> PageResponse:
    base_filter = build_created_by_filter(AuditLog, current_user)
    total, items = await query_audit_logs(
        db,
        page=page,
        page_size=page_size,
        q=q,
        module=module,
        action=action,
        resource_type=resource_type,
        base_filter=base_filter,
    )
    return PageResponse(total=total, page=page, page_size=page_size, items=items)
