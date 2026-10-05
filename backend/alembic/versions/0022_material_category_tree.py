"""material category tree and material category_id

Revision ID: 0022_material_category_tree
Revises: 0021_product_power
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0022_material_category_tree"
down_revision = "0021_product_power"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "material_categories",
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_material_categories_parent_id",
        "material_categories",
        "material_categories",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_material_categories_parent_id", "material_categories", ["parent_id"])

    op.add_column(
        "materials",
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_materials_category_id",
        "materials",
        "material_categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_materials_category_id", "materials", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_materials_category_id", table_name="materials")
    op.drop_constraint("fk_materials_category_id", "materials", type_="foreignkey")
    op.drop_column("materials", "category_id")

    op.drop_index("ix_material_categories_parent_id", table_name="material_categories")
    op.drop_constraint("fk_material_categories_parent_id", "material_categories", type_="foreignkey")
    op.drop_column("material_categories", "parent_id")
