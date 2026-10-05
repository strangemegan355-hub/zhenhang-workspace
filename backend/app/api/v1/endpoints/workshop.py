from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.services.workshop_board_service import get_workshop_board

router = APIRouter()


@router.get("/board")
async def workshop_board(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:workshop:read"))],
) -> dict:
    return await get_workshop_board(db)
