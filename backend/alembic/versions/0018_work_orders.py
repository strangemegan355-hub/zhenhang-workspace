"""work orders

Revision ID: 0018_work_orders
Revises: 0017_procurement_entries
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0018_work_orders"
down_revision = "0017_procurement_entries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("work_order_no", sa.String(length=64), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_desc", sa.String(length=255), nullable=False),
        sa.Column("process_node", sa.String(length=32), server_default="assembly", nullable=False),
        sa.Column("team", sa.String(length=120), nullable=True),
        sa.Column("owner_name", sa.String(length=120), nullable=True),
        sa.Column("claimed_by", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="todo", nullable=False),
        sa.Column("plan_start", sa.Date(), nullable=True),
        sa.Column("plan_end", sa.Date(), nullable=True),
        sa.Column("actual_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_hours", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("drawing_version", sa.String(length=32), nullable=True),
        sa.Column("exception_type", sa.String(length=32), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("work_order_no", name="uq_work_orders_work_order_no"),
    )
    op.create_index(op.f("ix_work_orders_project_id"), "work_orders", ["project_id"], unique=False)
    op.create_index(op.f("ix_work_orders_machine_id"), "work_orders", ["machine_id"], unique=False)
    op.create_index(op.f("ix_work_orders_process_node"), "work_orders", ["process_node"], unique=False)
    op.create_index(op.f("ix_work_orders_status"), "work_orders", ["status"], unique=False)
    op.create_index(op.f("ix_work_orders_plan_end"), "work_orders", ["plan_end"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_work_orders_plan_end"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_status"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_process_node"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_machine_id"), table_name="work_orders")
    op.drop_index(op.f("ix_work_orders_project_id"), table_name="work_orders")
    op.drop_table("work_orders")
