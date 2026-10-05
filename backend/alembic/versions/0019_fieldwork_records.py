"""fieldwork records

Revision ID: 0019_fieldwork_records
Revises: 0018_work_orders
Create Date: 2026-05-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0019_fieldwork_records"
down_revision = "0018_work_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fieldwork_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("record_no", sa.String(length=64), nullable=False),
        sa.Column("record_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="submitted", nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("material_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_on", sa.Date(), nullable=True),
        sa.Column("reporter_name", sa.String(length=120), nullable=True),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("qty", sa.Numeric(18, 4), nullable=True),
        sa.Column("hours", sa.Numeric(18, 4), nullable=True),
        sa.Column("urgency", sa.String(length=32), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("record_no", name="uq_fieldwork_records_record_no"),
    )
    op.create_index(op.f("ix_fieldwork_records_record_type"), "fieldwork_records", ["record_type"], unique=False)
    op.create_index(op.f("ix_fieldwork_records_status"), "fieldwork_records", ["status"], unique=False)
    op.create_index(op.f("ix_fieldwork_records_customer_id"), "fieldwork_records", ["customer_id"], unique=False)
    op.create_index(op.f("ix_fieldwork_records_project_id"), "fieldwork_records", ["project_id"], unique=False)
    op.create_index(op.f("ix_fieldwork_records_machine_id"), "fieldwork_records", ["machine_id"], unique=False)
    op.create_index(op.f("ix_fieldwork_records_material_id"), "fieldwork_records", ["material_id"], unique=False)
    op.create_index(op.f("ix_fieldwork_records_occurred_on"), "fieldwork_records", ["occurred_on"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_fieldwork_records_occurred_on"), table_name="fieldwork_records")
    op.drop_index(op.f("ix_fieldwork_records_material_id"), table_name="fieldwork_records")
    op.drop_index(op.f("ix_fieldwork_records_machine_id"), table_name="fieldwork_records")
    op.drop_index(op.f("ix_fieldwork_records_project_id"), table_name="fieldwork_records")
    op.drop_index(op.f("ix_fieldwork_records_customer_id"), table_name="fieldwork_records")
    op.drop_index(op.f("ix_fieldwork_records_status"), table_name="fieldwork_records")
    op.drop_index(op.f("ix_fieldwork_records_record_type"), table_name="fieldwork_records")
    op.drop_table("fieldwork_records")
