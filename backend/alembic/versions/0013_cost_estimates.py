"""cost estimates (internal costing sheets)

Revision ID: 0013_cost_estimates
Revises: 0012_master_standards
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0013_cost_estimates"
down_revision = "0012_master_standards"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cost_estimates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("estimate_no", sa.String(length=64), nullable=False),
        sa.Column("product_name", sa.String(length=160), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("drawing_no", sa.String(length=120), nullable=True),
        sa.Column("qty", sa.Numeric(18, 4), server_default="1", nullable=False),
        sa.Column("delivery_note", sa.String(length=255), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("outsource_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("logistics_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("scrap_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("overhead_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("profit_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("tax_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("material_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("machine_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("labor_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("other_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("base_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("scrap_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("overhead_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("total_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("profit_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("before_tax", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("tax_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("final_total", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("unit_final", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("estimate_no", name="uq_cost_estimates_estimate_no"),
    )
    op.create_index("ix_cost_estimates_estimate_no", "cost_estimates", ["estimate_no"])
    op.create_index("ix_cost_estimates_product_name", "cost_estimates", ["product_name"])
    op.create_index("ix_cost_estimates_customer_id", "cost_estimates", ["customer_id"])
    op.create_index("ix_cost_estimates_is_deleted", "cost_estimates", ["is_deleted"])

    op.create_table(
        "cost_estimate_material_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cost_estimate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("spec", sa.String(length=200), nullable=True),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit", sa.String(length=32), server_default="EA", nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("line_total", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["cost_estimate_id"], ["cost_estimates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_cost_estimate_material_lines_cost_estimate_id", "cost_estimate_material_lines", ["cost_estimate_id"])

    op.create_table(
        "cost_estimate_machine_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cost_estimate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("spec", sa.String(length=200), nullable=True),
        sa.Column("power_kw", sa.String(length=64), nullable=True),
        sa.Column("unit_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), server_default="1", nullable=False),
        sa.Column("line_total", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["cost_estimate_id"], ["cost_estimates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_cost_estimate_machine_lines_cost_estimate_id", "cost_estimate_machine_lines", ["cost_estimate_id"])

    op.create_table(
        "cost_estimate_process_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("cost_estimate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_name", sa.String(length=120), nullable=False),
        sa.Column("equipment", sa.String(length=120), nullable=True),
        sa.Column("hours", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("rate", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("line_total", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["cost_estimate_id"], ["cost_estimates.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_cost_estimate_process_lines_cost_estimate_id", "cost_estimate_process_lines", ["cost_estimate_id"])


def downgrade() -> None:
    op.drop_index("ix_cost_estimate_process_lines_cost_estimate_id", table_name="cost_estimate_process_lines")
    op.drop_table("cost_estimate_process_lines")
    op.drop_index("ix_cost_estimate_machine_lines_cost_estimate_id", table_name="cost_estimate_machine_lines")
    op.drop_table("cost_estimate_machine_lines")
    op.drop_index("ix_cost_estimate_material_lines_cost_estimate_id", table_name="cost_estimate_material_lines")
    op.drop_table("cost_estimate_material_lines")
    op.drop_index("ix_cost_estimates_is_deleted", table_name="cost_estimates")
    op.drop_index("ix_cost_estimates_customer_id", table_name="cost_estimates")
    op.drop_index("ix_cost_estimates_product_name", table_name="cost_estimates")
    op.drop_index("ix_cost_estimates_estimate_no", table_name="cost_estimates")
    op.drop_table("cost_estimates")
