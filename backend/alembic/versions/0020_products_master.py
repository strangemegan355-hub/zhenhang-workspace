"""products master data

Revision ID: 0020_products_master
Revises: 0019_fieldwork_records
Create Date: 2026-06-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0020_products_master"
down_revision = "0019_fieldwork_records"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["product_categories.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_product_categories_code"),
    )
    op.create_index("ix_product_categories_code", "product_categories", ["code"])
    op.create_index("ix_product_categories_name", "product_categories", ["name"])
    op.create_index("ix_product_categories_is_deleted", "product_categories", ["is_deleted"])

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("spec", sa.String(length=200), nullable=True),
        sa.Column("unit", sa.String(length=32), server_default="EA", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("reference_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("reference_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_bom_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["product_categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["machine_id"], ["machines.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["default_bom_id"], ["machine_boms.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_products_code"),
    )
    op.create_index("ix_products_code", "products", ["code"])
    op.create_index("ix_products_name", "products", ["name"])
    op.create_index("ix_products_is_deleted", "products", ["is_deleted"])

    op.create_table(
        "product_cost_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scrap_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("overhead_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_product_cost_templates_code"),
    )
    op.create_index("ix_product_cost_templates_code", "product_cost_templates", ["code"])
    op.create_index("ix_product_cost_templates_is_deleted", "product_cost_templates", ["is_deleted"])

    op.create_table(
        "product_cost_template_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_type", sa.String(length=32), server_default="material", nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("unit", sa.String(length=32), server_default="EA", nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), server_default="1", nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["product_cost_templates.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_product_cost_template_lines_template_id", "product_cost_template_lines", ["template_id"])

    op.create_table(
        "product_price_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cost_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("margin_rate", sa.Numeric(7, 4), server_default="0.2", nullable=False),
        sa.Column("tax_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("discount_rate", sa.Numeric(7, 4), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cost_template_id"], ["product_cost_templates.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("code", name="uq_product_price_templates_code"),
    )
    op.create_index("ix_product_price_templates_code", "product_price_templates", ["code"])
    op.create_index("ix_product_price_templates_is_deleted", "product_price_templates", ["is_deleted"])

    op.create_table(
        "product_price_template_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=False),
        sa.Column("unit", sa.String(length=32), server_default="EA", nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), server_default="1", nullable=False),
        sa.Column("unit_cost", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("unit_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["product_price_templates.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_product_price_template_lines_template_id", "product_price_template_lines", ["template_id"])

    op.add_column("products", sa.Column("default_cost_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("products", sa.Column("default_price_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_products_default_cost_template",
        "products",
        "product_cost_templates",
        ["default_cost_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_products_default_price_template",
        "products",
        "product_price_templates",
        ["default_price_template_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.add_column("quotes", sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("quotes", sa.Column("cost_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("quotes", sa.Column("price_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_quotes_product_id", "quotes", "products", ["product_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(
        "fk_quotes_cost_template_id",
        "quotes",
        "product_cost_templates",
        ["cost_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_quotes_price_template_id",
        "quotes",
        "product_price_templates",
        ["price_template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_quotes_product_id", "quotes", ["product_id"])

    op.add_column("quote_items", sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_quote_items_product_id", "quote_items", "products", ["product_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_quote_items_product_id", "quote_items", type_="foreignkey")
    op.drop_column("quote_items", "product_id")
    op.drop_index("ix_quotes_product_id", table_name="quotes")
    op.drop_constraint("fk_quotes_price_template_id", "quotes", type_="foreignkey")
    op.drop_constraint("fk_quotes_cost_template_id", "quotes", type_="foreignkey")
    op.drop_constraint("fk_quotes_product_id", "quotes", type_="foreignkey")
    op.drop_column("quotes", "price_template_id")
    op.drop_column("quotes", "cost_template_id")
    op.drop_column("quotes", "product_id")
    op.drop_constraint("fk_products_default_price_template", "products", type_="foreignkey")
    op.drop_constraint("fk_products_default_cost_template", "products", type_="foreignkey")
    op.drop_column("products", "default_price_template_id")
    op.drop_column("products", "default_cost_template_id")
    op.drop_table("product_price_template_lines")
    op.drop_table("product_price_templates")
    op.drop_table("product_cost_template_lines")
    op.drop_table("product_cost_templates")
    op.drop_table("products")
    op.drop_table("product_categories")
