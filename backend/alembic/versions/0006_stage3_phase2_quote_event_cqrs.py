"""stage3 phase2: quote approvals, event resilience, file policies

Revision ID: 0006_stage3_phase2_quote_event_cqrs
Revises: 0005_stage3_ddd_foundation
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006_stage3_phase2_quote_event_cqrs"
down_revision = "0005_stage3_ddd_foundation"
branch_labels = None
depends_on = None


def _audit_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    ]


def upgrade() -> None:
    op.add_column("domain_events", sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("domain_events", sa.Column("dead_letter", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.create_index(op.f("ix_domain_events_dead_letter"), "domain_events", ["dead_letter"], unique=False)

    op.add_column("quote_versions", sa.Column("analysis_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("quote_versions", sa.Column("total_cost", sa.Numeric(18, 4), server_default="0", nullable=False))
    op.add_column("quote_versions", sa.Column("profit_amount", sa.Numeric(18, 4), server_default="0", nullable=False))
    op.add_column("quote_versions", sa.Column("profit_rate", sa.Numeric(10, 4), server_default="0", nullable=False))

    op.create_table(
        "approval_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("biz_type", sa.String(length=64), server_default="quote", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_approval_templates_biz_type"), "approval_templates", ["biz_type"], unique=False)
    op.create_index(op.f("ix_approval_templates_code"), "approval_templates", ["code"], unique=True)
    op.create_index(op.f("ix_approval_templates_is_deleted"), "approval_templates", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_approval_templates_name"), "approval_templates", ["name"], unique=False)

    op.add_column("quotes", sa.Column("approval_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("quotes", sa.Column("current_approval_order", sa.Integer(), server_default="0", nullable=False))
    op.create_index(op.f("ix_quotes_approval_template_id"), "quotes", ["approval_template_id"], unique=False)
    op.create_foreign_key(
        "fk_quotes_approval_template_id_approval_templates",
        "quotes",
        "approval_templates",
        ["approval_template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "approval_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_order", sa.Integer(), nullable=False),
        sa.Column("node_name", sa.String(length=120), nullable=False),
        sa.Column("approver_role_code", sa.String(length=64), nullable=True),
        sa.Column("sign_mode", sa.String(length=16), server_default="orsign", nullable=False),
        sa.Column("dynamic_approver_expr", sa.String(length=255), nullable=True),
        sa.Column("min_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("max_amount", sa.Numeric(18, 4), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["template_id"], ["approval_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("template_id", "node_order", name="uq_approval_nodes_template_order"),
    )
    op.create_index(op.f("ix_approval_nodes_approver_role_code"), "approval_nodes", ["approver_role_code"], unique=False)
    op.create_index(op.f("ix_approval_nodes_is_deleted"), "approval_nodes", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_approval_nodes_template_id"), "approval_nodes", ["template_id"], unique=False)

    op.create_table(
        "approval_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["approval_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["node_id"], ["approval_nodes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approver_id"], ["sys_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_approval_records_approver_id"), "approval_records", ["approver_id"], unique=False)
    op.create_index(op.f("ix_approval_records_is_deleted"), "approval_records", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_approval_records_node_id"), "approval_records", ["node_id"], unique=False)
    op.create_index(op.f("ix_approval_records_quote_id"), "approval_records", ["quote_id"], unique=False)
    op.create_index(op.f("ix_approval_records_template_id"), "approval_records", ["template_id"], unique=False)

    op.create_table(
        "quote_export_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("format", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["file_objects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_quote_export_tasks_file_id"), "quote_export_tasks", ["file_id"], unique=False)
    op.create_index(op.f("ix_quote_export_tasks_format"), "quote_export_tasks", ["format"], unique=False)
    op.create_index(op.f("ix_quote_export_tasks_is_deleted"), "quote_export_tasks", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_quote_export_tasks_quote_id"), "quote_export_tasks", ["quote_id"], unique=False)

    op.create_table(
        "file_preview_caches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("preview_url", sa.String(length=500), nullable=False),
        sa.Column("thumb_url", sa.String(length=500), nullable=True),
        sa.Column("expires_at", sa.String(length=64), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["file_id"], ["file_objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_file_preview_caches_cache_key"), "file_preview_caches", ["cache_key"], unique=True)
    op.create_index(op.f("ix_file_preview_caches_file_id"), "file_preview_caches", ["file_id"], unique=False)
    op.create_index(op.f("ix_file_preview_caches_is_deleted"), "file_preview_caches", ["is_deleted"], unique=False)

    op.create_table(
        "file_lifecycle_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("retention_days", sa.Integer(), server_default="365", nullable=False),
        sa.Column("archive_after_days", sa.Integer(), nullable=True),
        sa.Column("delete_after_days", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_file_lifecycle_policies_category"), "file_lifecycle_policies", ["category"], unique=True)
    op.create_index(op.f("ix_file_lifecycle_policies_is_deleted"), "file_lifecycle_policies", ["is_deleted"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_file_lifecycle_policies_is_deleted"), table_name="file_lifecycle_policies")
    op.drop_index(op.f("ix_file_lifecycle_policies_category"), table_name="file_lifecycle_policies")
    op.drop_table("file_lifecycle_policies")
    op.drop_index(op.f("ix_file_preview_caches_is_deleted"), table_name="file_preview_caches")
    op.drop_index(op.f("ix_file_preview_caches_file_id"), table_name="file_preview_caches")
    op.drop_index(op.f("ix_file_preview_caches_cache_key"), table_name="file_preview_caches")
    op.drop_table("file_preview_caches")
    op.drop_index(op.f("ix_quote_export_tasks_quote_id"), table_name="quote_export_tasks")
    op.drop_index(op.f("ix_quote_export_tasks_is_deleted"), table_name="quote_export_tasks")
    op.drop_index(op.f("ix_quote_export_tasks_format"), table_name="quote_export_tasks")
    op.drop_index(op.f("ix_quote_export_tasks_file_id"), table_name="quote_export_tasks")
    op.drop_table("quote_export_tasks")
    op.drop_index(op.f("ix_approval_records_template_id"), table_name="approval_records")
    op.drop_index(op.f("ix_approval_records_quote_id"), table_name="approval_records")
    op.drop_index(op.f("ix_approval_records_node_id"), table_name="approval_records")
    op.drop_index(op.f("ix_approval_records_is_deleted"), table_name="approval_records")
    op.drop_index(op.f("ix_approval_records_approver_id"), table_name="approval_records")
    op.drop_table("approval_records")
    op.drop_index(op.f("ix_approval_nodes_template_id"), table_name="approval_nodes")
    op.drop_index(op.f("ix_approval_nodes_is_deleted"), table_name="approval_nodes")
    op.drop_index(op.f("ix_approval_nodes_approver_role_code"), table_name="approval_nodes")
    op.drop_table("approval_nodes")
    op.drop_constraint("fk_quotes_approval_template_id_approval_templates", "quotes", type_="foreignkey")
    op.drop_index(op.f("ix_quotes_approval_template_id"), table_name="quotes")
    op.drop_column("quotes", "current_approval_order")
    op.drop_column("quotes", "approval_template_id")
    op.drop_index(op.f("ix_approval_templates_name"), table_name="approval_templates")
    op.drop_index(op.f("ix_approval_templates_is_deleted"), table_name="approval_templates")
    op.drop_index(op.f("ix_approval_templates_code"), table_name="approval_templates")
    op.drop_index(op.f("ix_approval_templates_biz_type"), table_name="approval_templates")
    op.drop_table("approval_templates")
    op.drop_column("quote_versions", "profit_rate")
    op.drop_column("quote_versions", "profit_amount")
    op.drop_column("quote_versions", "total_cost")
    op.drop_column("quote_versions", "analysis_snapshot")
    op.drop_index(op.f("ix_domain_events_dead_letter"), table_name="domain_events")
    op.drop_column("domain_events", "dead_letter")
    op.drop_column("domain_events", "retry_count")
