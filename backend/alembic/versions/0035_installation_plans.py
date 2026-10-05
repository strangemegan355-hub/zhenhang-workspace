"""add installation_plans

Revision ID: 0035_installation_plans
Revises: 0034_acceptance
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0035_installation_plans"
down_revision = "0034_acceptance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "installation_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("equipment_unit_id", sa.Uuid(), nullable=False),
        sa.Column("planned_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="planned"),
        sa.Column("install_items", postgresql.JSONB, nullable=True),
        sa.Column("commissioning_items", postgresql.JSONB, nullable=True),
        sa.Column("customer_representative", sa.String(length=120), nullable=True),
        sa.Column("customer_accepted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("customer_accepted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_unit_id"], ["equipment_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installation_plans_equipment_unit_id", "installation_plans", ["equipment_unit_id"])
    op.create_index("ix_installation_plans_is_deleted", "installation_plans", ["is_deleted"])


def downgrade() -> None:
    op.drop_table("installation_plans")
