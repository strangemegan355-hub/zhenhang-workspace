"""project actual costs

Revision ID: 0016_project_actual_costs
Revises: 0015_projects_master
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0016_project_actual_costs"
down_revision = "0015_projects_master"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project_actual_costs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cost_category", sa.String(length=32), nullable=False),
        sa.Column("cost_item_code", sa.String(length=32), nullable=True),
        sa.Column("cost_item_name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("source", sa.String(length=64), server_default="采购", nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("procurement_ref", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_project_actual_costs_project_id"), "project_actual_costs", ["project_id"], unique=False)
    op.create_index(op.f("ix_project_actual_costs_cost_category"), "project_actual_costs", ["cost_category"], unique=False)
    op.create_index(op.f("ix_project_actual_costs_supplier_id"), "project_actual_costs", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_project_actual_costs_occurred_on"), "project_actual_costs", ["occurred_on"], unique=False)
    op.create_index(op.f("ix_project_actual_costs_procurement_ref"), "project_actual_costs", ["procurement_ref"], unique=False)
    op.create_index(
        "uq_project_actual_costs_procurement_ref",
        "project_actual_costs",
        ["procurement_ref"],
        unique=True,
        postgresql_where=sa.text("procurement_ref IS NOT NULL AND is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_project_actual_costs_procurement_ref", table_name="project_actual_costs")
    op.drop_index(op.f("ix_project_actual_costs_procurement_ref"), table_name="project_actual_costs")
    op.drop_index(op.f("ix_project_actual_costs_occurred_on"), table_name="project_actual_costs")
    op.drop_index(op.f("ix_project_actual_costs_supplier_id"), table_name="project_actual_costs")
    op.drop_index(op.f("ix_project_actual_costs_cost_category"), table_name="project_actual_costs")
    op.drop_index(op.f("ix_project_actual_costs_project_id"), table_name="project_actual_costs")
    op.drop_table("project_actual_costs")
