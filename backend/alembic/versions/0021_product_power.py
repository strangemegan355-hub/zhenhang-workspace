"""add product power field

Revision ID: 0021_product_power
Revises: 0020_products_master
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0021_product_power"
down_revision = "0020_products_master"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("power", sa.String(length=64), nullable=True))
    op.create_index("ix_products_power", "products", ["power"])


def downgrade() -> None:
    op.drop_index("ix_products_power", table_name="products")
    op.drop_column("products", "power")
