"""add subsystem to bom items

Revision ID: 0031_add_subsystem_to_bom_items
Revises: 0030_equipment_units
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0031_add_subsystem_to_bom_items"
down_revision = "0030_equipment_units"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "machine_bom_items",
        sa.Column("subsystem", sa.String(length=32), nullable=True),
    )
    op.create_index("ix_machine_bom_items_subsystem", "machine_bom_items", ["subsystem"])


def downgrade() -> None:
    op.drop_index("ix_machine_bom_items_subsystem", table_name="machine_bom_items")
    op.drop_column("machine_bom_items", "subsystem")
