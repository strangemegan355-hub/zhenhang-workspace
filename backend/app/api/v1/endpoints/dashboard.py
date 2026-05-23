from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardOverview
from app.services import dashboard_service as dash_svc

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
async def dashboard_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("dashboard:view"))],
) -> DashboardOverview:
    data = await dash_svc.get_dashboard_overview(db, current)
    return DashboardOverview.model_validate(data)
