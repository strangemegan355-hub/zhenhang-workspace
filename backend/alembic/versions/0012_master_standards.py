"""units and material categories master data

Revision ID: 0012_master_standards
Revises: 0011_suppliers_master
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012_master_standards"
down_revision = "0011_suppliers_master"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.UniqueConstraint("code", name="uq_units_code"),
    )
    op.create_index("ix_units_code", "units", ["code"])
    op.create_index("ix_units_name", "units", ["name"])
    op.create_index("ix_units_is_deleted", "units", ["is_deleted"])

    op.create_table(
        "material_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("scope", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.UniqueConstraint("code", name="uq_material_categories_code"),
    )
    op.create_index("ix_material_categories_code", "material_categories", ["code"])
    op.create_index("ix_material_categories_name", "material_categories", ["name"])
    op.create_index("ix_material_categories_is_deleted", "material_categories", ["is_deleted"])

    op.execute(
        sa.text(
            """
            INSERT INTO units (id, code, name, status, is_deleted)
            VALUES
              (gen_random_uuid(), 'EA', '个/件', 'active', false),
              (gen_random_uuid(), 'KG', '千克', 'active', false),
              (gen_random_uuid(), 'M', '米', 'active', false),
              (gen_random_uuid(), 'SET', '套', 'active', false)
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO material_categories (id, code, name, scope, status, is_deleted)
            VALUES
              (gen_random_uuid(), 'STEEL', '钢材', '结构件/板材', 'active', false),
              (gen_random_uuid(), 'PURCHASE', '外购件', '标准件/电气件', 'active', false),
              (gen_random_uuid(), 'CAST', '铸件', '毛坯/加工件', 'active', false)
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_material_categories_is_deleted", table_name="material_categories")
    op.drop_index("ix_material_categories_name", table_name="material_categories")
    op.drop_index("ix_material_categories_code", table_name="material_categories")
    op.drop_table("material_categories")
    op.drop_index("ix_units_is_deleted", table_name="units")
    op.drop_index("ix_units_name", table_name="units")
    op.drop_index("ix_units_code", table_name="units")
    op.drop_table("units")
