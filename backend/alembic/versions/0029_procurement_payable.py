"""procurement payable approval

Revision ID: 0029_procurement_payable
Revises: 0028_fieldwork_repair_billing
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0029_procurement_payable"
down_revision = "0028_fieldwork_repair_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "procurement_entries",
        sa.Column("payable_status", sa.String(length=32), server_default="none", nullable=False),
    )
    op.create_index("ix_procurement_entries_payable_status", "procurement_entries", ["payable_status"])

    op.create_table(
        "procurement_payable_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("procurement_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("approval_status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("payable_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["procurement_entry_id"], ["procurement_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["sys_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["payable_entry_id"], ["accounting_entries.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_procurement_payable_requests_entry_id",
        "procurement_payable_requests",
        ["procurement_entry_id"],
    )
    op.create_index(
        "ix_procurement_payable_requests_approval_status",
        "procurement_payable_requests",
        ["approval_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_procurement_payable_requests_approval_status", table_name="procurement_payable_requests")
    op.drop_index("ix_procurement_payable_requests_entry_id", table_name="procurement_payable_requests")
    op.drop_table("procurement_payable_requests")
    op.drop_index("ix_procurement_entries_payable_status", table_name="procurement_entries")
    op.drop_column("procurement_entries", "payable_status")
