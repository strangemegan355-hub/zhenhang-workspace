from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.machine import Machine, MachineBom
    from app.models.user import User


class Quote(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "quotes"

    quote_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    machine_id: Mapped[UUID] = mapped_column(ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False, index=True)
    bom_id: Mapped[UUID | None] = mapped_column(ForeignKey("machine_boms.id", ondelete="SET NULL"), nullable=True, index=True)
    approval_template_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("approval_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_approval_order: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    workflow_state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", server_default="draft", index=True)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="CNY", server_default="CNY")
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped["Customer"] = relationship()
    machine: Mapped["Machine"] = relationship()
    bom: Mapped["MachineBom | None"] = relationship()
    approval_template: Mapped["ApprovalTemplate | None"] = relationship()
    versions: Mapped[list[QuoteVersion]] = relationship(back_populates="quote")
    approvals: Mapped[list[QuoteApproval]] = relationship(back_populates="quote")
    creator: Mapped["User | None"] = relationship(foreign_keys="Quote.created_by", lazy="joined")


class QuoteVersion(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "quote_versions"
    __table_args__ = (UniqueConstraint("quote_id", "version_no", name="uq_quote_versions_quote_version"),)

    quote_id: Mapped[UUID] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    version_no: Mapped[int] = mapped_column(nullable=False)
    bom_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cost_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    analysis_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    total_cost: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    profit_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    profit_rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0, server_default="0")
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    quote: Mapped[Quote] = relationship(back_populates="versions")
    items: Mapped[list[QuoteItem]] = relationship(back_populates="quote_version")
    creator: Mapped["User | None"] = relationship(foreign_keys="QuoteVersion.created_by", lazy="joined")


class QuoteItem(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "quote_items"

    quote_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("quote_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(160), nullable=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="manual", server_default="manual")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    quote_version: Mapped[QuoteVersion] = relationship(back_populates="items")
    creator: Mapped["User | None"] = relationship(foreign_keys="QuoteItem.created_by", lazy="joined")


class QuoteApproval(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "quote_approvals"

    quote_id: Mapped[UUID] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id: Mapped[UUID] = mapped_column(ForeignKey("sys_users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    quote: Mapped[Quote] = relationship(back_populates="approvals")
    approver: Mapped["User"] = relationship(foreign_keys=[approver_id])
    creator: Mapped["User | None"] = relationship(foreign_keys="QuoteApproval.created_by", lazy="joined")


class ApprovalTemplate(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "approval_templates"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    biz_type: Mapped[str] = mapped_column(String(64), nullable=False, default="quote", server_default="quote", index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    nodes: Mapped[list["ApprovalNode"]] = relationship(back_populates="template")
    creator: Mapped["User | None"] = relationship(foreign_keys="ApprovalTemplate.created_by", lazy="joined")


class ApprovalNode(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "approval_nodes"
    __table_args__ = (UniqueConstraint("template_id", "node_order", name="uq_approval_nodes_template_order"),)

    template_id: Mapped[UUID] = mapped_column(ForeignKey("approval_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    node_order: Mapped[int] = mapped_column(nullable=False)
    node_name: Mapped[str] = mapped_column(String(120), nullable=False)
    approver_role_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sign_mode: Mapped[str] = mapped_column(String(16), nullable=False, default="orsign", server_default="orsign")
    dynamic_approver_expr: Mapped[str | None] = mapped_column(String(255), nullable=True)
    min_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0, server_default="0")
    max_amount: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)

    template: Mapped[ApprovalTemplate] = relationship(back_populates="nodes")
    creator: Mapped["User | None"] = relationship(foreign_keys="ApprovalNode.created_by", lazy="joined")


class ApprovalRecord(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "approval_records"

    quote_id: Mapped[UUID] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[UUID] = mapped_column(ForeignKey("approval_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    node_id: Mapped[UUID | None] = mapped_column(ForeignKey("approval_nodes.id", ondelete="SET NULL"), nullable=True, index=True)
    approver_id: Mapped[UUID] = mapped_column(ForeignKey("sys_users.id", ondelete="RESTRICT"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    acted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    quote: Mapped[Quote] = relationship()
    template: Mapped[ApprovalTemplate | None] = relationship()
    node: Mapped[ApprovalNode | None] = relationship()
    approver: Mapped["User"] = relationship(foreign_keys=[approver_id])
    creator: Mapped["User | None"] = relationship(foreign_keys="ApprovalRecord.created_by", lazy="joined")


class QuoteExportTask(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "quote_export_tasks"

    quote_id: Mapped[UUID] = mapped_column(ForeignKey("quotes.id", ondelete="CASCADE"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(16), nullable=False, index=True)  # pdf/xlsx
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending")
    file_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_objects.id", ondelete="SET NULL"), nullable=True, index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    quote: Mapped[Quote] = relationship()
    creator: Mapped["User | None"] = relationship(foreign_keys="QuoteExportTask.created_by", lazy="joined")
