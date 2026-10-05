"""customer quotation fields on quotes

Revision ID: 0014_customer_quotation
Revises: 0013_cost_estimates
Create Date: 2026-05-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0014_customer_quotation"
down_revision = "0013_cost_estimates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quotes",
        sa.Column("quote_kind", sa.String(length=32), server_default="industrial", nullable=False),
    )
    op.add_column("quotes", sa.Column("tax_rate", sa.Numeric(7, 4), nullable=True))
    op.alter_column("quotes", "machine_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.create_index("ix_quotes_quote_kind", "quotes", ["quote_kind"])

    op.add_column("quote_items", sa.Column("machine_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("quote_items", sa.Column("power_kw", sa.String(length=64), nullable=True))
    op.create_foreign_key(
        "fk_quote_items_machine_id_machines",
        "quote_items",
        "machines",
        ["machine_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_quote_items_machine_id", "quote_items", ["machine_id"])

    op.execute(
        sa.text(
            """
            INSERT INTO customers (id, code, name, status, is_deleted)
            SELECT gen_random_uuid(), 'WALK-IN', '零散客户（通用报价）', 'active', false
            WHERE NOT EXISTS (SELECT 1 FROM customers WHERE code = 'WALK-IN' AND is_deleted = false)
            """
        )
    )
    op.execute(
        sa.text(
            """
            INSERT INTO machines (id, code, machine_code, name, status, is_deleted)
            SELECT gen_random_uuid(), 'GENERIC', 'GENERIC', '通用报价占位', 'active', false
            WHERE NOT EXISTS (SELECT 1 FROM machines WHERE code = 'GENERIC' AND is_deleted = false)
            """
        )
    )


def downgrade() -> None:
    op.drop_index("ix_quote_items_machine_id", table_name="quote_items")
    op.drop_constraint("fk_quote_items_machine_id_machines", "quote_items", type_="foreignkey")
    op.drop_column("quote_items", "power_kw")
    op.drop_column("quote_items", "machine_id")

    op.drop_index("ix_quotes_quote_kind", table_name="quotes")
    op.drop_column("quotes", "tax_rate")
    op.drop_column("quotes", "quote_kind")
    op.alter_column("quotes", "machine_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
