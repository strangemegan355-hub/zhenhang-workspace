from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.project import Project
    from app.models.user import User


class CostEstimate(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "cost_estimates"

    estimate_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    product_spec: Mapped[str | None] = mapped_column(String(200), nullable=True)
    power_kw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    drawing_no: Mapped[str | None] = mapped_column(String(120), nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=1, server_default="1")
    delivery_note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft")

    outsource_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    logistics_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    scrap_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    overhead_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    profit_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), nullable=False, default=0, server_default="0")

    material_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    machine_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    labor_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    other_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    base_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    scrap_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    overhead_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    profit_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    before_tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    final_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    unit_final: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")

    customer: Mapped[Customer | None] = relationship(lazy="joined")
    project: Mapped[Project | None] = relationship(lazy="joined")
    material_lines: Mapped[list[CostEstimateMaterialLine]] = relationship(
        back_populates="cost_estimate",
        cascade="all, delete-orphan",
        order_by="CostEstimateMaterialLine.sort_order",
    )
    machine_lines: Mapped[list[CostEstimateMachineLine]] = relationship(
        back_populates="cost_estimate",
        cascade="all, delete-orphan",
        order_by="CostEstimateMachineLine.sort_order",
    )
    process_lines: Mapped[list[CostEstimateProcessLine]] = relationship(
        back_populates="cost_estimate",
        cascade="all, delete-orphan",
        order_by="CostEstimateProcessLine.sort_order",
    )
    creator: Mapped[User | None] = relationship(foreign_keys="CostEstimate.created_by", lazy="joined")


class CostEstimateMaterialLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cost_estimate_material_lines"

    cost_estimate_id: Mapped[UUID] = mapped_column(ForeignKey("cost_estimates.id", ondelete="CASCADE"), index=True)
    material_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(200), nullable=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="EA", server_default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    cost_estimate: Mapped[CostEstimate] = relationship(back_populates="material_lines")


class CostEstimateMachineLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cost_estimate_machine_lines"

    cost_estimate_id: Mapped[UUID] = mapped_column(ForeignKey("cost_estimates.id", ondelete="CASCADE"), index=True)
    machine_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("machines.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(200), nullable=True)
    power_kw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=1, server_default="1")
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    cost_estimate: Mapped[CostEstimate] = relationship(back_populates="machine_lines")


class CostEstimateProcessLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cost_estimate_process_lines"

    cost_estimate_id: Mapped[UUID] = mapped_column(ForeignKey("cost_estimates.id", ondelete="CASCADE"), index=True)
    process_name: Mapped[str] = mapped_column(String(120), nullable=False)
    equipment: Mapped[str | None] = mapped_column(String(120), nullable=True)
    hours: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    cost_estimate: Mapped[CostEstimate] = relationship(back_populates="process_lines")
