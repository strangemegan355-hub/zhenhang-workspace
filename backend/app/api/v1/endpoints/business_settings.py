from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_any_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.business_settings import BusinessSettingsRead, BusinessSettingsUpdate
from app.services import business_settings_service as svc

router = APIRouter()


@router.get("", response_model=BusinessSettingsRead)
async def get_business_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[
        User,
        Depends(
            require_any_permission(
                "platform:config:read",
                "business:settings:read",
            )
        ),
    ],
) -> BusinessSettingsRead:
    return await svc.get_business_settings(db)


@router.put("", response_model=BusinessSettingsRead)
async def update_business_settings(
    payload: BusinessSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[
        User,
        Depends(
            require_any_permission(
                "platform:config:update",
                "business:settings:update",
            )
        ),
    ],
) -> BusinessSettingsRead:
    return await svc.update_business_settings(db, payload, current)
