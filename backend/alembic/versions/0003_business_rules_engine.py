"""stage2 enhancement: rules engine, audit and workflow

Revision ID: 0003_business_rules_engine
Revises: 0002_master_data_center
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003_business_rules_engine"
down_revision = "0002_master_data_center"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("machines", sa.Column("machine_code", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_machines_machine_code"), "machines", ["machine_code"], unique=True)

    op.add_column("machine_boms", sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("machine_boms", sa.Column("effective_date", sa.Date(), nullable=True))
    op.add_column("machine_boms", sa.Column("total_cost", sa.Numeric(18, 4), server_default="0", nullable=False))
    op.create_index(op.f("ix_machine_boms_is_active"), "machine_boms", ["is_active"], unique=False)

    op.add_column("machine_bom_items", sa.Column("unit_cost", sa.Numeric(18, 4), server_default="0", nullable=False))
    op.add_column("machine_bom_items", sa.Column("line_total", sa.Numeric(18, 4), server_default="0", nullable=False))

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("module", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_created_by"), "audit_logs", ["created_by"], unique=False)
    op.create_index(op.f("ix_audit_logs_is_deleted"), "audit_logs", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_audit_logs_module"), "audit_logs", ["module"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_resource_type"), "audit_logs", ["resource_type"], unique=False)

    op.create_table(
        "workflow_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_start", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_end", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("entity_type", "code", name="uq_workflow_states_entity_type_code"),
    )
    op.create_index(op.f("ix_workflow_states_code"), "workflow_states", ["code"], unique=False)
    op.create_index(op.f("ix_workflow_states_created_by"), "workflow_states", ["created_by"], unique=False)
    op.create_index(op.f("ix_workflow_states_entity_type"), "workflow_states", ["entity_type"], unique=False)
    op.create_index(op.f("ix_workflow_states_is_deleted"), "workflow_states", ["is_deleted"], unique=False)

    op.create_table(
        "workflow_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("from_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_state_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_code", sa.String(length=64), nullable=False),
        sa.Column("action_name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_state_id"], ["workflow_states.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_state_id"], ["workflow_states.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "entity_type",
            "from_state_id",
            "to_state_id",
            "action_code",
            name="uq_workflow_transitions_unique_action",
        ),
    )
    op.create_index(op.f("ix_workflow_transitions_action_code"), "workflow_transitions", ["action_code"], unique=False)
    op.create_index(op.f("ix_workflow_transitions_created_by"), "workflow_transitions", ["created_by"], unique=False)
    op.create_index(op.f("ix_workflow_transitions_entity_type"), "workflow_transitions", ["entity_type"], unique=False)
    op.create_index(op.f("ix_workflow_transitions_from_state_id"), "workflow_transitions", ["from_state_id"], unique=False)
    op.create_index(op.f("ix_workflow_transitions_is_deleted"), "workflow_transitions", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_workflow_transitions_to_state_id"), "workflow_transitions", ["to_state_id"], unique=False)

    op.execute("UPDATE machines SET machine_code = code WHERE machine_code IS NULL")
    op.alter_column("machines", "machine_code", nullable=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_transitions_to_state_id"), table_name="workflow_transitions")
    op.drop_index(op.f("ix_workflow_transitions_is_deleted"), table_name="workflow_transitions")
    op.drop_index(op.f("ix_workflow_transitions_from_state_id"), table_name="workflow_transitions")
    op.drop_index(op.f("ix_workflow_transitions_entity_type"), table_name="workflow_transitions")
    op.drop_index(op.f("ix_workflow_transitions_created_by"), table_name="workflow_transitions")
    op.drop_index(op.f("ix_workflow_transitions_action_code"), table_name="workflow_transitions")
    op.drop_table("workflow_transitions")
    op.drop_index(op.f("ix_workflow_states_is_deleted"), table_name="workflow_states")
    op.drop_index(op.f("ix_workflow_states_entity_type"), table_name="workflow_states")
    op.drop_index(op.f("ix_workflow_states_created_by"), table_name="workflow_states")
    op.drop_index(op.f("ix_workflow_states_code"), table_name="workflow_states")
    op.drop_table("workflow_states")
    op.drop_index(op.f("ix_audit_logs_resource_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_resource_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_module"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_is_deleted"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_created_by"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_column("machine_bom_items", "line_total")
    op.drop_column("machine_bom_items", "unit_cost")
    op.drop_index(op.f("ix_machine_boms_is_active"), table_name="machine_boms")
    op.drop_column("machine_boms", "total_cost")
    op.drop_column("machine_boms", "effective_date")
    op.drop_column("machine_boms", "is_active")
    op.drop_index(op.f("ix_machines_machine_code"), table_name="machines")
    op.drop_column("machines", "machine_code")
