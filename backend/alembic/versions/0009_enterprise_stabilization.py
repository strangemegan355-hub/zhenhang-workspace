"""enterprise stabilization: tenant, event archive, MES foundation

Revision ID: 0009_enterprise_stabilization
Revises: 0008_production_hardening_realtime
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009_enterprise_stabilization"
down_revision = "0008_production_hardening_realtime"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.UniqueConstraint("code", name="uq_tenants_code"),
    )

    for table in ("sys_users", "sys_departments", "customers", "machines", "quotes", "realtime_events"):
        op.add_column(table, sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_tenant_id",
            table,
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index(f"ix_{table}_tenant_id", table, ["tenant_id"])

    # ix_realtime_events_created_at already created in 0008_production_hardening_realtime

    op.create_table(
        "realtime_events_archive",
        sa.Column("sequence", sa.BigInteger(), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("envelope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audience", sa.String(length=16), nullable=False),
        sa.Column("audience_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("audience_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_realtime_events_archive_archived_at", "realtime_events_archive", ["archived_at"])

    op.create_table(
        "mes_equipment_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("equipment_code", sa.String(length=64), nullable=False),
        sa.Column("signal_key", sa.String(length=64), nullable=False),
        sa.Column("signal_value", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("quality", sa.String(length=16), server_default="good", nullable=False),
        sa.Column("source", sa.String(length=32), server_default="mes", nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_mes_equipment_signals_collected", "mes_equipment_signals", ["collected_at"])

    op.create_table(
        "mes_oee_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("line_id", sa.String(length=32), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("availability", sa.Numeric(7, 4), nullable=False),
        sa.Column("performance", sa.Numeric(7, 4), nullable=False),
        sa.Column("quality", sa.Numeric(7, 4), nullable=False),
        sa.Column("oee", sa.Numeric(7, 4), nullable=False),
        sa.Column("source", sa.String(length=32), server_default="erp", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("mes_oee_snapshots")
    op.drop_table("mes_equipment_signals")
    op.drop_table("realtime_events_archive")
    for table in ("realtime_events", "quotes", "machines", "customers", "sys_departments", "sys_users"):
        op.drop_constraint(f"fk_{table}_tenant_id", table, type_="foreignkey")
        op.drop_index(f"ix_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")
    op.drop_table("tenants")
