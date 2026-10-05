"""add acceptance_templates, acceptance_records, punch_list_items

Revision ID: 0034_acceptance
Revises: 0033_quote_item_selected_options
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0034_acceptance"
down_revision = "0033_quote_item_selected_options"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "acceptance_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("template_type", sa.String(length=8), nullable=False),
        sa.Column("machine_id", sa.Uuid(), nullable=True),
        sa.Column("items", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_acceptance_templates_template_type", "acceptance_templates", ["template_type"])
    op.create_index("ix_acceptance_templates_machine_id", "acceptance_templates", ["machine_id"])
    op.create_index("ix_acceptance_templates_is_deleted", "acceptance_templates", ["is_deleted"])

    op.create_table(
        "acceptance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("template_id", sa.Uuid(), nullable=False),
        sa.Column("equipment_unit_id", sa.Uuid(), nullable=False),
        sa.Column("record_no", sa.String(length=64), nullable=False),
        sa.Column("test_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("inspector_name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="in_progress"),
        sa.Column("items", postgresql.JSONB, nullable=True),
        sa.Column("overall_result", sa.Text(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["template_id"], ["acceptance_templates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["equipment_unit_id"], ["equipment_units.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_acceptance_records_template_id", "acceptance_records", ["template_id"])
    op.create_index("ix_acceptance_records_equipment_unit_id", "acceptance_records", ["equipment_unit_id"])
    op.create_index("ix_acceptance_records_record_no", "acceptance_records", ["record_no"], unique=True)
    op.create_index("ix_acceptance_records_status", "acceptance_records", ["status"])
    op.create_index("ix_acceptance_records_is_deleted", "acceptance_records", ["is_deleted"])

    op.create_table(
        "punch_list_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=12), nullable=False, server_default="minor"),
        sa.Column("status", sa.String(length=12), nullable=False, server_default="open"),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["record_id"], ["acceptance_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_punch_list_items_record_id", "punch_list_items", ["record_id"])
    op.create_index("ix_punch_list_items_is_deleted", "punch_list_items", ["is_deleted"])


def downgrade() -> None:
    op.drop_table("punch_list_items")
    op.drop_table("acceptance_records")
    op.drop_table("acceptance_templates")
