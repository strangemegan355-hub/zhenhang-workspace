"""add option_groups and option_items

Revision ID: 0032_option_groups
Revises: 0031_add_subsystem_to_bom_items
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0032_option_groups"
down_revision = "0031_add_subsystem_to_bom_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "option_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("machine_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_option_groups_machine_id", "option_groups", ["machine_id"])
    op.create_index("ix_option_groups_is_deleted", "option_groups", ["is_deleted"])

    op.create_table(
        "option_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("option_group_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("price_adjustment", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["option_group_id"], ["option_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_option_items_option_group_id", "option_items", ["option_group_id"])
    op.create_index("ix_option_items_is_deleted", "option_items", ["is_deleted"])


def downgrade() -> None:
    op.drop_table("option_items")
    op.drop_table("option_groups")
