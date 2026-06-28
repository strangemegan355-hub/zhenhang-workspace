"""add aftersales_service_requests table

Revision ID: 0038
Revises: 0037
Create Date: 2026-06-28 22:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "aftersales_service_requests",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("request_no", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("customer_id", postgresql.UUID(), nullable=False),
        sa.Column("equipment_unit_id", postgresql.UUID(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("priority", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("assigned_to", postgresql.UUID(), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("completed_date", sa.Date(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("created_by", postgresql.UUID(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["assigned_to"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deleted_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["equipment_unit_id"], ["equipment_units.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_aftersales_request_no", "aftersales_service_requests", ["request_no"], unique=True)
    op.create_index("ix_aftersales_customer_id", "aftersales_service_requests", ["customer_id"])
    op.create_index("ix_aftersales_status", "aftersales_service_requests", ["status"])
    op.create_index("ix_aftersales_equipment_unit_id", "aftersales_service_requests", ["equipment_unit_id"])
    op.create_index("ix_aftersales_is_deleted", "aftersales_service_requests", ["is_deleted"])
    op.create_index("ix_aftersales_created_by", "aftersales_service_requests", ["created_by"])


def downgrade():
    op.drop_table("aftersales_service_requests")
