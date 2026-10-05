"""suppliers master data

Revision ID: 0011_suppliers_master
Revises: 0010_materials_master
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011_suppliers_master"
down_revision = "0010_materials_master"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("contact_name", sa.String(length=80), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.UniqueConstraint("code", name="uq_suppliers_code"),
    )
    op.create_index("ix_suppliers_code", "suppliers", ["code"])
    op.create_index("ix_suppliers_name", "suppliers", ["name"])
    op.create_index("ix_suppliers_contact_name", "suppliers", ["contact_name"])
    op.create_index("ix_suppliers_phone", "suppliers", ["phone"])
    op.create_index("ix_suppliers_is_deleted", "suppliers", ["is_deleted"])


def downgrade() -> None:
    op.drop_index("ix_suppliers_is_deleted", table_name="suppliers")
    op.drop_index("ix_suppliers_phone", table_name="suppliers")
    op.drop_index("ix_suppliers_contact_name", table_name="suppliers")
    op.drop_index("ix_suppliers_name", table_name="suppliers")
    op.drop_index("ix_suppliers_code", table_name="suppliers")
    op.drop_table("suppliers")
