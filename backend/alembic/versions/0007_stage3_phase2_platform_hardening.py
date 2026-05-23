"""stage3 phase2 platform hardening: workers, notifications, ai

Revision ID: 0007_stage3_phase2_platform_hardening
Revises: 0006_stage3_phase2_quote_event_cqrs
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_stage3_phase2_platform_hardening"
down_revision = "0006_stage3_phase2_quote_event_cqrs"
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
        "task_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("queue_name", sa.String(length=64), nullable=False),
        sa.Column("task_type", sa.String(length=128), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_retry", sa.Integer(), server_default="5", nullable=False),
        sa.Column("dead_letter", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_task_queue_dead_letter"), "task_queue", ["dead_letter"], unique=False)
    op.create_index(op.f("ix_task_queue_queue_name"), "task_queue", ["queue_name"], unique=False)
    op.create_index(op.f("ix_task_queue_status"), "task_queue", ["status"], unique=False)
    op.create_index(op.f("ix_task_queue_task_type"), "task_queue", ["task_type"], unique=False)
    op.create_index(op.f("ix_task_queue_is_deleted"), "task_queue", ["is_deleted"], unique=False)

    op.create_table(
        "job_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_name", sa.String(length=128), nullable=False),
        sa.Column("trigger_type", sa.String(length=32), server_default="manual", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="running", nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_job_executions_job_name"), "job_executions", ["job_name"], unique=False)
    op.create_index(op.f("ix_job_executions_status"), "job_executions", ["status"], unique=False)
    op.create_index(op.f("ix_job_executions_is_deleted"), "job_executions", ["is_deleted"], unique=False)

    op.create_table(
        "notification_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider_type", sa.String(length=32), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_notification_providers_code"), "notification_providers", ["code"], unique=True)
    op.create_index(op.f("ix_notification_providers_provider_type"), "notification_providers", ["provider_type"], unique=False)
    op.create_index(op.f("ix_notification_providers_is_deleted"), "notification_providers", ["is_deleted"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("channel", sa.String(length=32), server_default="inapp", nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("receiver_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["receiver_id"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["provider_id"], ["notification_providers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_notifications_biz_id"), "notifications", ["biz_id"], unique=False)
    op.create_index(op.f("ix_notifications_biz_type"), "notifications", ["biz_type"], unique=False)
    op.create_index(op.f("ix_notifications_channel"), "notifications", ["channel"], unique=False)
    op.create_index(op.f("ix_notifications_receiver_id"), "notifications", ["receiver_id"], unique=False)
    op.create_index(op.f("ix_notifications_provider_id"), "notifications", ["provider_id"], unique=False)
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"], unique=False)
    op.create_index(op.f("ix_notifications_is_deleted"), "notifications", ["is_deleted"], unique=False)

    op.create_table(
        "quote_pdf_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("template_path", sa.String(length=255), nullable=False),
        sa.Column("style_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_quote_pdf_templates_code"), "quote_pdf_templates", ["code"], unique=True)
    op.create_index(op.f("ix_quote_pdf_templates_is_deleted"), "quote_pdf_templates", ["is_deleted"], unique=False)

    op.create_table(
        "quote_excel_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("template_path", sa.String(length=255), nullable=False),
        sa.Column("style_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_default", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_quote_excel_templates_code"), "quote_excel_templates", ["code"], unique=True)
    op.create_index(op.f("ix_quote_excel_templates_is_deleted"), "quote_excel_templates", ["is_deleted"], unique=False)

    op.create_table(
        "ai_contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_ai_contexts_biz_id"), "ai_contexts", ["biz_id"], unique=False)
    op.create_index(op.f("ix_ai_contexts_biz_type"), "ai_contexts", ["biz_type"], unique=False)
    op.create_index(op.f("ix_ai_contexts_is_deleted"), "ai_contexts", ["is_deleted"], unique=False)

    op.create_table(
        "ai_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["context_id"], ["ai_contexts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["file_objects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_ai_documents_context_id"), "ai_documents", ["context_id"], unique=False)
    op.create_index(op.f("ix_ai_documents_file_id"), "ai_documents", ["file_id"], unique=False)
    op.create_index(op.f("ix_ai_documents_status"), "ai_documents", ["status"], unique=False)
    op.create_index(op.f("ix_ai_documents_is_deleted"), "ai_documents", ["is_deleted"], unique=False)

    op.create_table(
        "ai_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("vector", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_name", sa.String(length=64), server_default="pending", nullable=False),
        sa.Column("token_count", sa.Integer(), server_default="0", nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["document_id"], ["ai_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_ai_embeddings_document_id"), "ai_embeddings", ["document_id"], unique=False)
    op.create_index(op.f("ix_ai_embeddings_is_deleted"), "ai_embeddings", ["is_deleted"], unique=False)

    op.create_table(
        "embedding_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="pending", nullable=False),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dead_letter", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["document_id"], ["ai_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_embedding_tasks_dead_letter"), "embedding_tasks", ["dead_letter"], unique=False)
    op.create_index(op.f("ix_embedding_tasks_document_id"), "embedding_tasks", ["document_id"], unique=False)
    op.create_index(op.f("ix_embedding_tasks_status"), "embedding_tasks", ["status"], unique=False)
    op.create_index(op.f("ix_embedding_tasks_is_deleted"), "embedding_tasks", ["is_deleted"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_embedding_tasks_is_deleted"), table_name="embedding_tasks")
    op.drop_index(op.f("ix_embedding_tasks_status"), table_name="embedding_tasks")
    op.drop_index(op.f("ix_embedding_tasks_document_id"), table_name="embedding_tasks")
    op.drop_index(op.f("ix_embedding_tasks_dead_letter"), table_name="embedding_tasks")
    op.drop_table("embedding_tasks")
    op.drop_index(op.f("ix_ai_embeddings_is_deleted"), table_name="ai_embeddings")
    op.drop_index(op.f("ix_ai_embeddings_document_id"), table_name="ai_embeddings")
    op.drop_table("ai_embeddings")
    op.drop_index(op.f("ix_ai_documents_is_deleted"), table_name="ai_documents")
    op.drop_index(op.f("ix_ai_documents_status"), table_name="ai_documents")
    op.drop_index(op.f("ix_ai_documents_file_id"), table_name="ai_documents")
    op.drop_index(op.f("ix_ai_documents_context_id"), table_name="ai_documents")
    op.drop_table("ai_documents")
    op.drop_index(op.f("ix_ai_contexts_is_deleted"), table_name="ai_contexts")
    op.drop_index(op.f("ix_ai_contexts_biz_type"), table_name="ai_contexts")
    op.drop_index(op.f("ix_ai_contexts_biz_id"), table_name="ai_contexts")
    op.drop_table("ai_contexts")
    op.drop_index(op.f("ix_quote_excel_templates_is_deleted"), table_name="quote_excel_templates")
    op.drop_index(op.f("ix_quote_excel_templates_code"), table_name="quote_excel_templates")
    op.drop_table("quote_excel_templates")
    op.drop_index(op.f("ix_quote_pdf_templates_is_deleted"), table_name="quote_pdf_templates")
    op.drop_index(op.f("ix_quote_pdf_templates_code"), table_name="quote_pdf_templates")
    op.drop_table("quote_pdf_templates")
    op.drop_index(op.f("ix_notifications_is_deleted"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_status"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_provider_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_receiver_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_channel"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_biz_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_biz_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_notification_providers_is_deleted"), table_name="notification_providers")
    op.drop_index(op.f("ix_notification_providers_provider_type"), table_name="notification_providers")
    op.drop_index(op.f("ix_notification_providers_code"), table_name="notification_providers")
    op.drop_table("notification_providers")
    op.drop_index(op.f("ix_job_executions_is_deleted"), table_name="job_executions")
    op.drop_index(op.f("ix_job_executions_status"), table_name="job_executions")
    op.drop_index(op.f("ix_job_executions_job_name"), table_name="job_executions")
    op.drop_table("job_executions")
    op.drop_index(op.f("ix_task_queue_is_deleted"), table_name="task_queue")
    op.drop_index(op.f("ix_task_queue_task_type"), table_name="task_queue")
    op.drop_index(op.f("ix_task_queue_status"), table_name="task_queue")
    op.drop_index(op.f("ix_task_queue_queue_name"), table_name="task_queue")
    op.drop_index(op.f("ix_task_queue_dead_letter"), table_name="task_queue")
    op.drop_table("task_queue")
