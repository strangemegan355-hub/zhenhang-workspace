"""add due_date to accounting_entries

Revision ID: 0036
Revises: 0035_installation_plans
Create Date: 2026-06-28 21:22:00
"""
from alembic import op
import sqlalchemy as sa

revision = "0036"
down_revision = "0035_installation_plans"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("accounting_entries", sa.Column("due_date", sa.Date(), nullable=True))
    op.create_index("ix_accounting_entries_due_date", "accounting_entries", ["due_date"])


def downgrade():
    op.drop_index("ix_accounting_entries_due_date", table_name="accounting_entries")
    op.drop_column("accounting_entries", "due_date")
