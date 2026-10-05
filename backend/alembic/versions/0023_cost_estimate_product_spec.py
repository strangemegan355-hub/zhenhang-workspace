"""add product_spec and power_kw to cost_estimates

Revision ID: 0023_cost_estimate_product_spec
Revises: 0022_material_category_tree
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0023_cost_estimate_product_spec"
down_revision = "0022_material_category_tree"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cost_estimates", sa.Column("product_spec", sa.String(length=200), nullable=True))
    op.add_column("cost_estimates", sa.Column("power_kw", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("cost_estimates", "power_kw")
    op.drop_column("cost_estimates", "product_spec")
