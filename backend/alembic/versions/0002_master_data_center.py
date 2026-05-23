"""stage2 master data center: customers, machines, boms

Revision ID: 0002_master_data_center
Revises: 0001_initial
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_master_data_center"
down_revision = "0001_initial"
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
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("short_name", sa.String(length=80), nullable=True),
        sa.Column("industry", sa.String(length=80), nullable=True),
        sa.Column("level", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_customers_code"), "customers", ["code"], unique=True)
    op.create_index(op.f("ix_customers_created_by"), "customers", ["created_by"], unique=False)
    op.create_index(op.f("ix_customers_industry"), "customers", ["industry"], unique=False)
    op.create_index(op.f("ix_customers_is_deleted"), "customers", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_customers_level"), "customers", ["level"], unique=False)
    op.create_index(op.f("ix_customers_name"), "customers", ["name"], unique=False)

    op.create_table(
        "customer_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("position", sa.String(length=80), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("wechat", sa.String(length=80), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_customer_contacts_created_by"), "customer_contacts", ["created_by"], unique=False)
    op.create_index(op.f("ix_customer_contacts_customer_id"), "customer_contacts", ["customer_id"], unique=False)
    op.create_index(op.f("ix_customer_contacts_is_deleted"), "customer_contacts", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_customer_contacts_name"), "customer_contacts", ["name"], unique=False)
    op.create_index(op.f("ix_customer_contacts_phone"), "customer_contacts", ["phone"], unique=False)

    op.create_table(
        "customer_followups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("followup_type", sa.String(length=32), server_default="phone", nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("followup_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_followup_at", sa.DateTime(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["customer_contacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_customer_followups_contact_id"), "customer_followups", ["contact_id"], unique=False)
    op.create_index(op.f("ix_customer_followups_created_by"), "customer_followups", ["created_by"], unique=False)
    op.create_index(op.f("ix_customer_followups_customer_id"), "customer_followups", ["customer_id"], unique=False)
    op.create_index(op.f("ix_customer_followups_is_deleted"), "customer_followups", ["is_deleted"], unique=False)

    op.create_table(
        "machine_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["parent_id"], ["machine_categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_machine_categories_code"), "machine_categories", ["code"], unique=True)
    op.create_index(op.f("ix_machine_categories_created_by"), "machine_categories", ["created_by"], unique=False)
    op.create_index(op.f("ix_machine_categories_is_deleted"), "machine_categories", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_machine_categories_name"), "machine_categories", ["name"], unique=False)
    op.create_index(op.f("ix_machine_categories_parent_id"), "machine_categories", ["parent_id"], unique=False)

    op.create_table(
        "machines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("model_no", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["category_id"], ["machine_categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_machines_category_id"), "machines", ["category_id"], unique=False)
    op.create_index(op.f("ix_machines_code"), "machines", ["code"], unique=True)
    op.create_index(op.f("ix_machines_created_by"), "machines", ["created_by"], unique=False)
    op.create_index(op.f("ix_machines_is_deleted"), "machines", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_machines_model_no"), "machines", ["model_no"], unique=False)
    op.create_index(op.f("ix_machines_name"), "machines", ["name"], unique=False)

    op.create_table(
        "machine_parameters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("param_key", sa.String(length=64), nullable=False),
        sa.Column("param_name", sa.String(length=120), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_machine_parameters_created_by"), "machine_parameters", ["created_by"], unique=False)
    op.create_index(op.f("ix_machine_parameters_is_deleted"), "machine_parameters", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_machine_parameters_machine_id"), "machine_parameters", ["machine_id"], unique=False)
    op.create_index(op.f("ix_machine_parameters_param_key"), "machine_parameters", ["param_key"], unique=False)

    op.create_table(
        "machine_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=200), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_machine_images_created_by"), "machine_images", ["created_by"], unique=False)
    op.create_index(op.f("ix_machine_images_is_deleted"), "machine_images", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_machine_images_machine_id"), "machine_images", ["machine_id"], unique=False)

    op.create_table(
        "machine_boms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_machine_boms_created_by"), "machine_boms", ["created_by"], unique=False)
    op.create_index(op.f("ix_machine_boms_is_deleted"), "machine_boms", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_machine_boms_machine_id"), "machine_boms", ["machine_id"], unique=False)
    op.create_index(op.f("ix_machine_boms_version"), "machine_boms", ["version"], unique=False)

    op.create_table(
        "machine_bom_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bom_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=160), nullable=False),
        sa.Column("spec", sa.String(length=160), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("loss_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["bom_id"], ["machine_boms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["sys_users.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_machine_bom_items_bom_id"), "machine_bom_items", ["bom_id"], unique=False)
    op.create_index(op.f("ix_machine_bom_items_created_by"), "machine_bom_items", ["created_by"], unique=False)
    op.create_index(op.f("ix_machine_bom_items_is_deleted"), "machine_bom_items", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_machine_bom_items_item_code"), "machine_bom_items", ["item_code"], unique=False)
    op.create_index(op.f("ix_machine_bom_items_item_name"), "machine_bom_items", ["item_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_machine_bom_items_item_name"), table_name="machine_bom_items")
    op.drop_index(op.f("ix_machine_bom_items_item_code"), table_name="machine_bom_items")
    op.drop_index(op.f("ix_machine_bom_items_is_deleted"), table_name="machine_bom_items")
    op.drop_index(op.f("ix_machine_bom_items_created_by"), table_name="machine_bom_items")
    op.drop_index(op.f("ix_machine_bom_items_bom_id"), table_name="machine_bom_items")
    op.drop_table("machine_bom_items")
    op.drop_index(op.f("ix_machine_boms_version"), table_name="machine_boms")
    op.drop_index(op.f("ix_machine_boms_machine_id"), table_name="machine_boms")
    op.drop_index(op.f("ix_machine_boms_is_deleted"), table_name="machine_boms")
    op.drop_index(op.f("ix_machine_boms_created_by"), table_name="machine_boms")
    op.drop_table("machine_boms")
    op.drop_index(op.f("ix_machine_images_machine_id"), table_name="machine_images")
    op.drop_index(op.f("ix_machine_images_is_deleted"), table_name="machine_images")
    op.drop_index(op.f("ix_machine_images_created_by"), table_name="machine_images")
    op.drop_table("machine_images")
    op.drop_index(op.f("ix_machine_parameters_param_key"), table_name="machine_parameters")
    op.drop_index(op.f("ix_machine_parameters_machine_id"), table_name="machine_parameters")
    op.drop_index(op.f("ix_machine_parameters_is_deleted"), table_name="machine_parameters")
    op.drop_index(op.f("ix_machine_parameters_created_by"), table_name="machine_parameters")
    op.drop_table("machine_parameters")
    op.drop_index(op.f("ix_machines_name"), table_name="machines")
    op.drop_index(op.f("ix_machines_model_no"), table_name="machines")
    op.drop_index(op.f("ix_machines_is_deleted"), table_name="machines")
    op.drop_index(op.f("ix_machines_created_by"), table_name="machines")
    op.drop_index(op.f("ix_machines_code"), table_name="machines")
    op.drop_index(op.f("ix_machines_category_id"), table_name="machines")
    op.drop_table("machines")
    op.drop_index(op.f("ix_machine_categories_parent_id"), table_name="machine_categories")
    op.drop_index(op.f("ix_machine_categories_name"), table_name="machine_categories")
    op.drop_index(op.f("ix_machine_categories_is_deleted"), table_name="machine_categories")
    op.drop_index(op.f("ix_machine_categories_created_by"), table_name="machine_categories")
    op.drop_index(op.f("ix_machine_categories_code"), table_name="machine_categories")
    op.drop_table("machine_categories")
    op.drop_index(op.f("ix_customer_followups_is_deleted"), table_name="customer_followups")
    op.drop_index(op.f("ix_customer_followups_customer_id"), table_name="customer_followups")
    op.drop_index(op.f("ix_customer_followups_created_by"), table_name="customer_followups")
    op.drop_index(op.f("ix_customer_followups_contact_id"), table_name="customer_followups")
    op.drop_table("customer_followups")
    op.drop_index(op.f("ix_customer_contacts_phone"), table_name="customer_contacts")
    op.drop_index(op.f("ix_customer_contacts_name"), table_name="customer_contacts")
    op.drop_index(op.f("ix_customer_contacts_is_deleted"), table_name="customer_contacts")
    op.drop_index(op.f("ix_customer_contacts_customer_id"), table_name="customer_contacts")
    op.drop_index(op.f("ix_customer_contacts_created_by"), table_name="customer_contacts")
    op.drop_table("customer_contacts")
    op.drop_index(op.f("ix_customers_name"), table_name="customers")
    op.drop_index(op.f("ix_customers_level"), table_name="customers")
    op.drop_index(op.f("ix_customers_is_deleted"), table_name="customers")
    op.drop_index(op.f("ix_customers_industry"), table_name="customers")
    op.drop_index(op.f("ix_customers_created_by"), table_name="customers")
    op.drop_index(op.f("ix_customers_code"), table_name="customers")
    op.drop_table("customers")
