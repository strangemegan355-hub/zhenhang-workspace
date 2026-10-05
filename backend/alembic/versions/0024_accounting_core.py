"""accounting ledger core tables

Revision ID: 0024_accounting_core
Revises: 0023_cost_estimate_product_spec
Create Date: 2026-06-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0024_accounting_core"
down_revision = "0023_cost_estimate_product_spec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounting_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entry_no", sa.String(length=64), nullable=False),
        sa.Column("entry_kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("party_type", sa.String(length=16), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("settled_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=8), server_default="CNY", nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("booked_on", sa.Date(), nullable=False),
        sa.Column("is_backfill", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("source_type", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_no", sa.String(length=64), nullable=True),
        sa.Column("approval_status", sa.String(length=32), server_default="none", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("entry_no", name="uq_accounting_entries_entry_no"),
    )
    op.create_index("ix_accounting_entries_entry_no", "accounting_entries", ["entry_no"])
    op.create_index("ix_accounting_entries_entry_kind", "accounting_entries", ["entry_kind"])
    op.create_index("ix_accounting_entries_status", "accounting_entries", ["status"])
    op.create_index("ix_accounting_entries_customer_id", "accounting_entries", ["customer_id"])
    op.create_index("ix_accounting_entries_supplier_id", "accounting_entries", ["supplier_id"])
    op.create_index("ix_accounting_entries_project_id", "accounting_entries", ["project_id"])
    op.create_index("ix_accounting_entries_occurred_on", "accounting_entries", ["occurred_on"])
    op.create_index("ix_accounting_entries_source", "accounting_entries", ["source_type", "source_id"])

    op.create_table(
        "accounting_entry_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_name", sa.String(length=160), nullable=False),
        sa.Column("spec", sa.String(length=200), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("qty", sa.Numeric(18, 4), server_default="1", nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("line_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["entry_id"], ["accounting_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_accounting_entry_lines_entry_id", "accounting_entry_lines", ["entry_id"])


def downgrade() -> None:
    op.drop_index("ix_accounting_entry_lines_entry_id", table_name="accounting_entry_lines")
    op.drop_table("accounting_entry_lines")
    op.drop_index("ix_accounting_entries_source", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_occurred_on", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_project_id", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_supplier_id", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_customer_id", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_status", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_entry_kind", table_name="accounting_entries")
    op.drop_index("ix_accounting_entries_entry_no", table_name="accounting_entries")
    op.drop_table("accounting_entries")
