"""initial schema: departments, rbac, users

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sys_departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["sys_departments.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_sys_departments_code"), "sys_departments", ["code"], unique=True)
    op.create_index(op.f("ix_sys_departments_name"), "sys_departments", ["name"], unique=False)
    op.create_index(op.f("ix_sys_departments_parent_id"), "sys_departments", ["parent_id"], unique=False)

    op.create_table(
        "sys_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_sys_roles_code"), "sys_roles", ["code"], unique=True)

    op.create_table(
        "sys_permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=128), nullable=False),
        sa.Column("resource", sa.String(length=120), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(op.f("ix_sys_permissions_action"), "sys_permissions", ["action"], unique=False)
    op.create_index(op.f("ix_sys_permissions_code"), "sys_permissions", ["code"], unique=True)
    op.create_index(op.f("ix_sys_permissions_resource"), "sys_permissions", ["resource"], unique=False)

    op.create_table(
        "sys_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["sys_departments.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_sys_users_department_id"), "sys_users", ["department_id"], unique=False)
    op.create_index(op.f("ix_sys_users_email"), "sys_users", ["email"], unique=True)
    op.create_index(op.f("ix_sys_users_phone"), "sys_users", ["phone"], unique=False)
    op.create_index(op.f("ix_sys_users_username"), "sys_users", ["username"], unique=True)

    op.create_table(
        "sys_user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["sys_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["sys_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "role_id"),
    )

    op.create_table(
        "sys_role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["permission_id"], ["sys_permissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_id"], ["sys_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )


def downgrade() -> None:
    op.drop_table("sys_role_permissions")
    op.drop_table("sys_user_roles")
    op.drop_index(op.f("ix_sys_users_username"), table_name="sys_users")
    op.drop_index(op.f("ix_sys_users_phone"), table_name="sys_users")
    op.drop_index(op.f("ix_sys_users_email"), table_name="sys_users")
    op.drop_index(op.f("ix_sys_users_department_id"), table_name="sys_users")
    op.drop_table("sys_users")
    op.drop_index(op.f("ix_sys_permissions_resource"), table_name="sys_permissions")
    op.drop_index(op.f("ix_sys_permissions_code"), table_name="sys_permissions")
    op.drop_index(op.f("ix_sys_permissions_action"), table_name="sys_permissions")
    op.drop_table("sys_permissions")
    op.drop_index(op.f("ix_sys_roles_code"), table_name="sys_roles")
    op.drop_table("sys_roles")
    op.drop_index(op.f("ix_sys_departments_parent_id"), table_name="sys_departments")
    op.drop_index(op.f("ix_sys_departments_name"), table_name="sys_departments")
    op.drop_index(op.f("ix_sys_departments_code"), table_name="sys_departments")
    op.drop_table("sys_departments")
