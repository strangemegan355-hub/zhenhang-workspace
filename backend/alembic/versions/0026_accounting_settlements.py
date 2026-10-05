"""accounting settlements for receipt allocation

Revision ID: 0026_accounting_settlements
Revises: 0025_quote_receivable_request
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0026_accounting_settlements"
down_revision = "0025_quote_receivable_request"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounting_settlements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("receipt_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("receivable_entry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["receipt_entry_id"], ["accounting_entries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["receivable_entry_id"], ["accounting_entries.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_accounting_settlements_receipt_entry_id", "accounting_settlements", ["receipt_entry_id"])
    op.create_index("ix_accounting_settlements_receivable_entry_id", "accounting_settlements", ["receivable_entry_id"])


def downgrade() -> None:
    op.drop_index("ix_accounting_settlements_receivable_entry_id", table_name="accounting_settlements")
    op.drop_index("ix_accounting_settlements_receipt_entry_id", table_name="accounting_settlements")
    op.drop_table("accounting_settlements")
