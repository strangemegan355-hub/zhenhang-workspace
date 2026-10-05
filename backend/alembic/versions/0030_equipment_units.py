"""equipment units with serial number lifecycle

Revision ID: 0030_equipment_units
Revises: 0029_procurement_payable
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0030_equipment_units"
down_revision = "0029_procurement_payable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipment_units",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("serial_number", sa.String(length=80), unique=True, index=True, nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("build_status", sa.String(length=32), server_default="in_production", nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("build_start_date", sa.Date(), nullable=True),
        sa.Column("ship_date", sa.Date(), nullable=True),
        sa.Column("install_date", sa.Date(), nullable=True),
        sa.Column("acceptance_date", sa.Date(), nullable=True),
        sa.Column("warranty_expiry_date", sa.Date(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_equipment_units_machine_id", "equipment_units", ["machine_id"])
    op.create_index("ix_equipment_units_build_status", "equipment_units", ["build_status"])
    op.create_index("ix_equipment_units_project_id", "equipment_units", ["project_id"])
    op.create_index("ix_equipment_units_customer_id", "equipment_units", ["customer_id"])


def downgrade() -> None:
    op.drop_index("ix_equipment_units_customer_id", table_name="equipment_units")
    op.drop_index("ix_equipment_units_project_id", table_name="equipment_units")
    op.drop_index("ix_equipment_units_build_status", table_name="equipment_units")
    op.drop_index("ix_equipment_units_machine_id", table_name="equipment_units")
    op.drop_table("equipment_units")
