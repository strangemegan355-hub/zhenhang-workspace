"""add service_request_id FK to fieldwork_records

Revision ID: 0039
Revises: 0038
Create Date: 2026-06-29 08:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("fieldwork_records", sa.Column("service_request_id", postgresql.UUID(), nullable=True))
    op.create_index("ix_fieldwork_records_service_request_id", "fieldwork_records", ["service_request_id"])
    op.create_foreign_key(
        "fk_fieldwork_records_service_request_id",
        "fieldwork_records",
        "aftersales_service_requests",
        ["service_request_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_fieldwork_records_service_request_id", "fieldwork_records", type_="foreignkey")
    op.drop_index("ix_fieldwork_records_service_request_id", table_name="fieldwork_records")
    op.drop_column("fieldwork_records", "service_request_id")
