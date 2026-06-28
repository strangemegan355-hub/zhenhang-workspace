"""add supplier_ledger_accounts table

Revision ID: 0037
Revises: 0036
Create Date: 2026-06-28 21:30:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0037"
down_revision = "0036"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supplier_ledger_accounts",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", postgresql.UUID(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["deleted_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id"),
    )
    op.create_index("ix_supplier_ledger_accounts_supplier_id", "supplier_ledger_accounts", ["supplier_id"])
    op.create_index("ix_supplier_ledger_accounts_is_deleted", "supplier_ledger_accounts", ["is_deleted"])
    op.create_index("ix_supplier_ledger_accounts_created_by", "supplier_ledger_accounts", ["created_by"])


def downgrade():
    op.drop_table("supplier_ledger_accounts")
