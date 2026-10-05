"""fieldwork repair billing fields

Revision ID: 0028_fieldwork_repair_billing
Revises: 0027_customer_ledger_accounts
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0028_fieldwork_repair_billing"
down_revision = "0027_customer_ledger_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("fieldwork_records", sa.Column("repair_amount", sa.Numeric(18, 4), nullable=True))
    op.add_column(
        "fieldwork_records",
        sa.Column("receivable_entry_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_fieldwork_records_receivable_entry_id",
        "fieldwork_records",
        "accounting_entries",
        ["receivable_entry_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_fieldwork_records_receivable_entry_id", "fieldwork_records", ["receivable_entry_id"])


def downgrade() -> None:
    op.drop_index("ix_fieldwork_records_receivable_entry_id", table_name="fieldwork_records")
    op.drop_constraint("fk_fieldwork_records_receivable_entry_id", "fieldwork_records", type_="foreignkey")
    op.drop_column("fieldwork_records", "receivable_entry_id")
    op.drop_column("fieldwork_records", "repair_amount")
