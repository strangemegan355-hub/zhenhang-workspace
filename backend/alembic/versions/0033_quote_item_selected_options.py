"""add selected_options to quote_items

Revision ID: 0033_quote_item_selected_options
Revises: 0032_option_groups
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0033_quote_item_selected_options"
down_revision = "0032_option_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quote_items",
        sa.Column("selected_options", postgresql.JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("quote_items", "selected_options")
