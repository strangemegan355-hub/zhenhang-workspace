from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.services.mes_integration_service import ingest_equipment_signal, list_recent_signals, record_oee_snapshot

router = APIRouter()


class MesSignalIngest(BaseModel):
    equipment_code: str = Field(min_length=1, max_length=64)
    signal_key: str = Field(min_length=1, max_length=64)
    signal_value: float
    unit: str | None = Field(default=None, max_length=32)
    source: str = Field(default="mes", max_length=32)


@router.post("/equipment-signals", status_code=status.HTTP_201_CREATED)
async def post_equipment_signal(
    payload: MesSignalIngest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:update"))],
) -> dict:
    row = await ingest_equipment_signal(
        db,
        equipment_code=payload.equipment_code,
        signal_key=payload.signal_key,
        signal_value=payload.signal_value,
        unit=payload.unit,
        source=payload.source,
        tenant_id=getattr(current, "tenant_id", None),
    )
    await db.commit()
    return {"id": str(row.id), "equipment_code": row.equipment_code, "signal_key": row.signal_key}


@router.get("/equipment-signals")
async def get_equipment_signals(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_permissions("business:quote:read"))],
    equipment_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    rows = await list_recent_signals(db, equipment_code=equipment_code, limit=limit)
    return {
        "items": [
            {
                "equipment_code": r.equipment_code,
                "signal_key": r.signal_key,
                "signal_value": float(r.signal_value),
                "unit": r.unit,
                "quality": r.quality,
                "collected_at": r.collected_at.isoformat(),
            }
            for r in rows
        ]
    }


@router.post("/oee-snapshots", status_code=status.HTTP_201_CREATED)
async def post_oee_snapshot(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("business:quote:update"))],
    line_id: str = Query(..., max_length=32),
    availability: float = Query(..., ge=0, le=100),
    performance: float = Query(..., ge=0, le=100),
    quality: float = Query(..., ge=0, le=100),
) -> dict:
    row = await record_oee_snapshot(
        db,
        line_id=line_id,
        availability=availability,
        performance=performance,
        quality=quality,
        tenant_id=getattr(current, "tenant_id", None),
    )
    await db.commit()
    return {"line_id": row.line_id, "oee": float(row.oee)}
