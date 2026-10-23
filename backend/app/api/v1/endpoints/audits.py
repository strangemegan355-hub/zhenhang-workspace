from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.common import PageResponse
from app.services import audit_service as svc

router = APIRouter()


@router.get("", response_model=PageResponse[AuditLogRead], summary="Query audit logs with filters")
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:audit:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    module: str | None = Query(default=None, max_length=64),
    action: str | None = Query(default=None, max_length=64),
    resource_type: str | None = Query(default=None, max_length=64),
) -> PageResponse:
    return await svc.list_audit_logs(
        db,
        page=page,
        page_size=page_size,
        q=q,
        module=module,
        action=action,
        resource_type=resource_type,
        current_user=current,
    )
