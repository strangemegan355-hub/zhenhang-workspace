"""drop the non-unique indexes a unique index already covers

Round 104 found the models and migrations had drifted; round 105 added the missing indexes and foreign
keys. This handles the drop_index part of the remainder, and only the part that is safe on its own terms.

A unique index answers every query its non-unique twin over the same column does, so the non-unique one is
pure write overhead. Dropping those touches no rows.

Deliberately **not** here, from the same classification:

* indexes that do not exist under the name autogenerate expects — the model says `ix_work_orders_work_order_no`
  while the database has `uq_work_orders_work_order_no`; dropping would fail, so they are skipped;
* the nineteen indexes that are the only index of their shape (`ix_customers_tenant_id`,
  `ix_quotes_tenant_id`, `ix_acceptance_records_status` and others). The models are silent about them,
  which is not evidence that nothing uses them, and removing one takes away a query path.

Revision ID: 0041
Revises: 0040
Create Date: 2026-07-01 10:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # covered by uq_accounting_entries_entry_no
    op.drop_index(op.f("ix_accounting_entries_entry_no"), table_name="accounting_entries")
    # covered by uq_cost_estimates_estimate_no
    op.drop_index(op.f("ix_cost_estimates_estimate_no"), table_name="cost_estimates")
    # covered by uq_customer_ledger_accounts_customer_id
    op.drop_index(op.f("ix_customer_ledger_accounts_customer_id"), table_name="customer_ledger_accounts")
    # covered by uq_material_categories_code
    op.drop_index(op.f("ix_material_categories_code"), table_name="material_categories")
    # covered by uq_materials_code
    op.drop_index(op.f("ix_materials_code"), table_name="materials")
    # covered by uq_product_categories_code
    op.drop_index(op.f("ix_product_categories_code"), table_name="product_categories")
    # covered by uq_product_cost_templates_code
    op.drop_index(op.f("ix_product_cost_templates_code"), table_name="product_cost_templates")
    # covered by uq_product_price_templates_code
    op.drop_index(op.f("ix_product_price_templates_code"), table_name="product_price_templates")
    # covered by uq_products_code
    op.drop_index(op.f("ix_products_code"), table_name="products")
    # covered by uq_projects_project_no
    op.drop_index(op.f("ix_projects_project_no"), table_name="projects")
    # covered by uq_supplier_ledger_accounts_supplier_id
    op.drop_index(op.f("ix_supplier_ledger_accounts_supplier_id"), table_name="supplier_ledger_accounts")
    # covered by uq_suppliers_code
    op.drop_index(op.f("ix_suppliers_code"), table_name="suppliers")
    # covered by uq_units_code
    op.drop_index(op.f("ix_units_code"), table_name="units")


def downgrade() -> None:
    op.create_index(op.f("ix_accounting_entries_entry_no"), "accounting_entries", ["entry_no"], unique=False)
    op.create_index(op.f("ix_cost_estimates_estimate_no"), "cost_estimates", ["estimate_no"], unique=False)
    op.create_index(op.f("ix_customer_ledger_accounts_customer_id"), "customer_ledger_accounts", ["customer_id"], unique=False)
    op.create_index(op.f("ix_material_categories_code"), "material_categories", ["code"], unique=False)
    op.create_index(op.f("ix_materials_code"), "materials", ["code"], unique=False)
    op.create_index(op.f("ix_product_categories_code"), "product_categories", ["code"], unique=False)
    op.create_index(op.f("ix_product_cost_templates_code"), "product_cost_templates", ["code"], unique=False)
    op.create_index(op.f("ix_product_price_templates_code"), "product_price_templates", ["code"], unique=False)
    op.create_index(op.f("ix_products_code"), "products", ["code"], unique=False)
    op.create_index(op.f("ix_projects_project_no"), "projects", ["project_no"], unique=False)
    op.create_index(op.f("ix_supplier_ledger_accounts_supplier_id"), "supplier_ledger_accounts", ["supplier_id"], unique=False)
    op.create_index(op.f("ix_suppliers_code"), "suppliers", ["code"], unique=False)
    op.create_index(op.f("ix_units_code"), "units", ["code"], unique=False)
