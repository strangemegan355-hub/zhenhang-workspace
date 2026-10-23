"""MES / OEE integration foundation — equipment signals and OEE snapshots."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin


class MesEquipmentSignal(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "mes_equipment_signals"

    tenant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    equipment_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signal_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signal_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    quality: Mapped[str] = mapped_column(String(16), nullable=False, default="good", server_default="good")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mes", server_default="mes")
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class MesOeeSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "mes_oee_snapshots"

    tenant_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    line_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    availability: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    performance: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    quality: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    oee: Mapped[float] = mapped_column(Numeric(7, 4), nullable=False)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="erp", server_default="erp")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
