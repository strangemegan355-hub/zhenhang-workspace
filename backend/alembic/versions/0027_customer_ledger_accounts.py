"""customer ledger account registry

Revision ID: 0027_customer_ledger_accounts
Revises: 0026_accounting_settlements
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0027_customer_ledger_accounts"
down_revision = "0026_accounting_settlements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_ledger_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("customer_id", name="uq_customer_ledger_accounts_customer_id"),
    )
    op.create_index("ix_customer_ledger_accounts_customer_id", "customer_ledger_accounts", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_customer_ledger_accounts_customer_id", table_name="customer_ledger_accounts")
    op.drop_table("customer_ledger_accounts")
