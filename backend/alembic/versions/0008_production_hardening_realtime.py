"""production hardening: durable realtime event stream

Revision ID: 0008_production_hardening_realtime
Revises: 0007_stage3_phase2_platform_hardening
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_production_hardening_realtime"
down_revision = "0007_stage3_phase2_platform_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "realtime_events",
        sa.Column("sequence", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("envelope", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audience", sa.String(length=16), server_default="broadcast", nullable=False),
        sa.Column("audience_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("audience_department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("resource_owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("sequence"),
        sa.UniqueConstraint("event_id", name="uq_realtime_events_event_id"),
    )
    op.create_index("ix_realtime_events_channel", "realtime_events", ["channel"])
    op.create_index("ix_realtime_events_kind", "realtime_events", ["kind"])
    op.create_index("ix_realtime_events_audience_user_id", "realtime_events", ["audience_user_id"])
    op.create_index("ix_realtime_events_created_at", "realtime_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("realtime_events")
