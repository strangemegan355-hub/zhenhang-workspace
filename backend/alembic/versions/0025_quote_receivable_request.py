"""quote receivable request + quote receivable_status

Revision ID: 0025_quote_receivable_request
Revises: 0024_accounting_core
Create Date: 2026-06-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0025_quote_receivable_request"
down_revision = "0024_accounting_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quotes",
        sa.Column("receivable_status", sa.String(length=32), server_default="none", nullable=False),
    )
    op.create_index("ix_quotes_receivable_status", "quotes", ["receivable_status"])

    op.create_table(
        "quote_receivable_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requested_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("standard_amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("discount_rate_pct", sa.Numeric(10, 4), server_default="0", nullable=False),
        sa.Column("needs_boss_approval", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("approval_status", sa.String(length=32), server_default="none", nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("receivable_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by"], ["sys_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["approved_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["receivable_entry_id"], ["accounting_entries.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_quote_receivable_requests_quote_id", "quote_receivable_requests", ["quote_id"])
    op.create_index("ix_quote_receivable_requests_approval_status", "quote_receivable_requests", ["approval_status"])


def downgrade() -> None:
    op.drop_index("ix_quote_receivable_requests_approval_status", table_name="quote_receivable_requests")
    op.drop_index("ix_quote_receivable_requests_quote_id", table_name="quote_receivable_requests")
    op.drop_table("quote_receivable_requests")
    op.drop_index("ix_quotes_receivable_status", table_name="quotes")
    op.drop_column("quotes", "receivable_status")
