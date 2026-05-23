"""add role data scope foundation

Revision ID: 0004_role_data_scope
Revises: 0003_business_rules_engine
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_role_data_scope"
down_revision = "0003_business_rules_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sys_roles", sa.Column("data_scope", sa.String(length=32), server_default="self", nullable=False))
    op.execute("UPDATE sys_roles SET data_scope = 'all' WHERE code = 'admin'")


def downgrade() -> None:
    op.drop_column("sys_roles", "data_scope")
