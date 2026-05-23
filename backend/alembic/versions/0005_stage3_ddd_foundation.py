"""stage3 ddd foundation: events, configs, files, quotes

Revision ID: 0005_stage3_ddd_foundation
Revises: 0004_role_data_scope
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_stage3_ddd_foundation"
down_revision = "0004_role_data_scope"
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
    op.create_table(
        "domain_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_domain_events_event_type"), "domain_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_domain_events_aggregate_type"), "domain_events", ["aggregate_type"], unique=False)
    op.create_index(op.f("ix_domain_events_aggregate_id"), "domain_events", ["aggregate_id"], unique=False)
    op.create_index(op.f("ix_domain_events_is_deleted"), "domain_events", ["is_deleted"], unique=False)

    op.create_table(
        "system_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(length=32), server_default="string", nullable=False),
        sa.Column("group", sa.String(length=64), server_default="default", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_system_configs_group"), "system_configs", ["group"], unique=False)
    op.create_index(op.f("ix_system_configs_is_deleted"), "system_configs", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_system_configs_key"), "system_configs", ["key"], unique=True)

    op.create_table(
        "file_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bucket", sa.String(length=64), nullable=False),
        sa.Column("object_name", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_ext", sa.String(length=32), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(length=64), server_default="general", nullable=False),
        sa.Column("preview_url", sa.String(length=500), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_file_objects_category"), "file_objects", ["category"], unique=False)
    op.create_index(op.f("ix_file_objects_checksum"), "file_objects", ["checksum"], unique=False)
    op.create_index(op.f("ix_file_objects_file_name"), "file_objects", ["file_name"], unique=False)
    op.create_index(op.f("ix_file_objects_is_deleted"), "file_objects", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_file_objects_object_name"), "file_objects", ["object_name"], unique=True)

    op.create_table(
        "file_relations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=32), server_default="attachment", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["file_id"], ["file_objects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_file_relations_biz_id"), "file_relations", ["biz_id"], unique=False)
    op.create_index(op.f("ix_file_relations_biz_type"), "file_relations", ["biz_type"], unique=False)
    op.create_index(op.f("ix_file_relations_file_id"), "file_relations", ["file_id"], unique=False)
    op.create_index(op.f("ix_file_relations_is_deleted"), "file_relations", ["is_deleted"], unique=False)

    op.create_table(
        "quotes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_no", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("bom_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("workflow_state", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("currency", sa.String(length=8), server_default="CNY", nullable=False),
        sa.Column("total_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["bom_id"], ["machine_boms.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_quotes_bom_id"), "quotes", ["bom_id"], unique=False)
    op.create_index(op.f("ix_quotes_customer_id"), "quotes", ["customer_id"], unique=False)
    op.create_index(op.f("ix_quotes_is_deleted"), "quotes", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_quotes_machine_id"), "quotes", ["machine_id"], unique=False)
    op.create_index(op.f("ix_quotes_quote_no"), "quotes", ["quote_no"], unique=True)
    op.create_index(op.f("ix_quotes_title"), "quotes", ["title"], unique=False)
    op.create_index(op.f("ix_quotes_workflow_state"), "quotes", ["workflow_state"], unique=False)

    op.create_table(
        "quote_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_no", sa.Integer(), nullable=False),
        sa.Column("bom_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("cost_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("total_amount", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("quote_id", "version_no", name="uq_quote_versions_quote_version"),
    )
    op.create_index(op.f("ix_quote_versions_is_current"), "quote_versions", ["is_current"], unique=False)
    op.create_index(op.f("ix_quote_versions_is_deleted"), "quote_versions", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_quote_versions_quote_id"), "quote_versions", ["quote_id"], unique=False)

    op.create_table(
        "quote_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("spec", sa.String(length=160), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("line_total", sa.Numeric(18, 4), nullable=False),
        sa.Column("source_type", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["quote_version_id"], ["quote_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_quote_items_is_deleted"), "quote_items", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_quote_items_item_code"), "quote_items", ["item_code"], unique=False)
    op.create_index(op.f("ix_quote_items_quote_version_id"), "quote_items", ["quote_version_id"], unique=False)

    op.create_table(
        "quote_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("quote_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approver_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["quote_id"], ["quotes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approver_id"], ["sys_users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_quote_approvals_approver_id"), "quote_approvals", ["approver_id"], unique=False)
    op.create_index(op.f("ix_quote_approvals_is_deleted"), "quote_approvals", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_quote_approvals_quote_id"), "quote_approvals", ["quote_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_quote_approvals_quote_id"), table_name="quote_approvals")
    op.drop_index(op.f("ix_quote_approvals_is_deleted"), table_name="quote_approvals")
    op.drop_index(op.f("ix_quote_approvals_approver_id"), table_name="quote_approvals")
    op.drop_table("quote_approvals")
    op.drop_index(op.f("ix_quote_items_quote_version_id"), table_name="quote_items")
    op.drop_index(op.f("ix_quote_items_item_code"), table_name="quote_items")
    op.drop_index(op.f("ix_quote_items_is_deleted"), table_name="quote_items")
    op.drop_table("quote_items")
    op.drop_index(op.f("ix_quote_versions_quote_id"), table_name="quote_versions")
    op.drop_index(op.f("ix_quote_versions_is_deleted"), table_name="quote_versions")
    op.drop_index(op.f("ix_quote_versions_is_current"), table_name="quote_versions")
    op.drop_table("quote_versions")
    op.drop_index(op.f("ix_quotes_workflow_state"), table_name="quotes")
    op.drop_index(op.f("ix_quotes_title"), table_name="quotes")
    op.drop_index(op.f("ix_quotes_quote_no"), table_name="quotes")
    op.drop_index(op.f("ix_quotes_machine_id"), table_name="quotes")
    op.drop_index(op.f("ix_quotes_is_deleted"), table_name="quotes")
    op.drop_index(op.f("ix_quotes_customer_id"), table_name="quotes")
    op.drop_index(op.f("ix_quotes_bom_id"), table_name="quotes")
    op.drop_table("quotes")
    op.drop_index(op.f("ix_file_relations_is_deleted"), table_name="file_relations")
    op.drop_index(op.f("ix_file_relations_file_id"), table_name="file_relations")
    op.drop_index(op.f("ix_file_relations_biz_type"), table_name="file_relations")
    op.drop_index(op.f("ix_file_relations_biz_id"), table_name="file_relations")
    op.drop_table("file_relations")
    op.drop_index(op.f("ix_file_objects_object_name"), table_name="file_objects")
    op.drop_index(op.f("ix_file_objects_is_deleted"), table_name="file_objects")
    op.drop_index(op.f("ix_file_objects_file_name"), table_name="file_objects")
    op.drop_index(op.f("ix_file_objects_checksum"), table_name="file_objects")
    op.drop_index(op.f("ix_file_objects_category"), table_name="file_objects")
    op.drop_table("file_objects")
    op.drop_index(op.f("ix_system_configs_key"), table_name="system_configs")
    op.drop_index(op.f("ix_system_configs_is_deleted"), table_name="system_configs")
    op.drop_index(op.f("ix_system_configs_group"), table_name="system_configs")
    op.drop_table("system_configs")
    op.drop_index(op.f("ix_domain_events_is_deleted"), table_name="domain_events")
    op.drop_index(op.f("ix_domain_events_aggregate_id"), table_name="domain_events")
    op.drop_index(op.f("ix_domain_events_aggregate_type"), table_name="domain_events")
    op.drop_index(op.f("ix_domain_events_event_type"), table_name="domain_events")
    op.drop_table("domain_events")
