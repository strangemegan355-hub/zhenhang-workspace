"""materials master data

Revision ID: 0010_materials_master
Revises: 0009_enterprise_stabilization
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010_materials_master"
down_revision = "0009_enterprise_stabilization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("spec", sa.String(length=200), nullable=True),
        sa.Column("unit", sa.String(length=32), server_default="EA", nullable=False),
        sa.Column("reference_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.UniqueConstraint("code", name="uq_materials_code"),
    )
    op.create_index("ix_materials_code", "materials", ["code"])
    op.create_index("ix_materials_name", "materials", ["name"])
    op.create_index("ix_materials_spec", "materials", ["spec"])
    op.create_index("ix_materials_category", "materials", ["category"])
    op.create_index("ix_materials_is_deleted", "materials", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_materials_is_deleted", table_name="materials")
    op.drop_index("ix_materials_category", table_name="materials")
    op.drop_index("ix_materials_spec", table_name="materials")
    op.drop_index("ix_materials_name", table_name="materials")
    op.drop_index("ix_materials_code", table_name="materials")
    op.drop_table("materials")
