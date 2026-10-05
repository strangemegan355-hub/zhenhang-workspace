"""projects master and quote/cost estimate linkage

Revision ID: 0015_projects_master
Revises: 0014_customer_quotation
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0015_projects_master"
down_revision = "0014_customer_quotation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("project_no", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("stage", sa.String(length=32), server_default="lead", nullable=False),
        sa.Column("owner_name", sa.String(length=120), nullable=True),
        sa.Column("primary_quote_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("project_no", name="uq_projects_project_no"),
    )
    op.create_index("ix_projects_project_no", "projects", ["project_no"])
    op.create_index("ix_projects_name", "projects", ["name"])
    op.create_index("ix_projects_customer_id", "projects", ["customer_id"])
    op.create_index("ix_projects_stage", "projects", ["stage"])
    op.create_index("ix_projects_is_deleted", "projects", ["is_deleted"])

    op.add_column("quotes", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_quotes_project_id_projects",
        "quotes",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_quotes_project_id", "quotes", ["project_id"])

    op.create_foreign_key(
        "fk_projects_primary_quote_id_quotes",
        "projects",
        "quotes",
        ["primary_quote_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_projects_primary_quote_id", "projects", ["primary_quote_id"])

    op.add_column("cost_estimates", sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_cost_estimates_project_id_projects",
        "cost_estimates",
        "projects",
        ["project_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_cost_estimates_project_id", "cost_estimates", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_cost_estimates_project_id", table_name="cost_estimates")
    op.drop_constraint("fk_cost_estimates_project_id_projects", "cost_estimates", type_="foreignkey")
    op.drop_column("cost_estimates", "project_id")

    op.drop_index("ix_projects_primary_quote_id", table_name="projects")
    op.drop_constraint("fk_projects_primary_quote_id_quotes", "projects", type_="foreignkey")

    op.drop_index("ix_quotes_project_id", table_name="quotes")
    op.drop_constraint("fk_quotes_project_id_projects", "quotes", type_="foreignkey")
    op.drop_column("quotes", "project_id")

    op.drop_index("ix_projects_is_deleted", table_name="projects")
    op.drop_index("ix_projects_stage", table_name="projects")
    op.drop_index("ix_projects_customer_id", table_name="projects")
    op.drop_index("ix_projects_name", table_name="projects")
    op.drop_index("ix_projects_project_no", table_name="projects")
    op.drop_table("projects")
