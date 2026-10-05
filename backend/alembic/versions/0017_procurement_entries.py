"""procurement entries

Revision ID: 0017_procurement_entries
Revises: 0016_project_actual_costs
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0017_procurement_entries"
down_revision = "0016_project_actual_costs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "procurement_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("request_no", sa.String(length=64), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("lead_days", sa.Integer(), server_default="7", nullable=False),
        sa.Column("need_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="planned", nullable=False),
        sa.Column("transferred_to_actual", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("request_no", name="uq_procurement_entries_request_no"),
    )
    op.create_index(op.f("ix_procurement_entries_project_id"), "procurement_entries", ["project_id"], unique=False)
    op.create_index(op.f("ix_procurement_entries_material_id"), "procurement_entries", ["material_id"], unique=False)
    op.create_index(op.f("ix_procurement_entries_supplier_id"), "procurement_entries", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_procurement_entries_status"), "procurement_entries", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_procurement_entries_status"), table_name="procurement_entries")
    op.drop_index(op.f("ix_procurement_entries_supplier_id"), table_name="procurement_entries")
    op.drop_index(op.f("ix_procurement_entries_material_id"), table_name="procurement_entries")
    op.drop_index(op.f("ix_procurement_entries_project_id"), table_name="procurement_entries")
    op.drop_table("procurement_entries")
