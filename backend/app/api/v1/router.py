from fastapi import APIRouter

from app.api.v1.endpoints import (
    acceptance,
    accounting,
    aftersales,
    ai,
    approval_hub,
    audits,
    auth,
    boms,
    business_settings,
    configs,
    cost_estimates,
    customers,
    dashboard,
    equipment_units,
    fieldwork_records,
    files,
    health,
    installation_plans,
    machines,
    material_categories,
    materials,
    mes,
    notifications,
    option_groups,
    procurement_entries,
    product_categories,
    product_cost_templates,
    product_price_templates,
    products,
    project_actual_costs,
    projects,
    quotes,
    realtime,
    suppliers,
    units,
    users,
    work_orders,
    workflows,
    workshop,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["system.health"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["business.dashboard"])
api_router.include_router(auth.router, prefix="/auth", tags=["system.auth"])
api_router.include_router(users.router, prefix="/users", tags=["system.user"])
api_router.include_router(customers.router, prefix="/customers", tags=["master.customer"])
api_router.include_router(machines.router, prefix="/machines", tags=["master.machine"])
api_router.include_router(equipment_units.router, prefix="/equipment-units", tags=["master.equipment_unit"])
api_router.include_router(boms.router, prefix="/boms", tags=["master.bom"])
api_router.include_router(materials.router, prefix="/materials", tags=["master.material"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["master.supplier"])
api_router.include_router(units.router, prefix="/units", tags=["master.standard"])
api_router.include_router(material_categories.router, prefix="/material-categories", tags=["master.standard"])
api_router.include_router(product_categories.router, prefix="/product-categories", tags=["master.product"])
api_router.include_router(products.router, prefix="/products", tags=["master.product"])
api_router.include_router(product_cost_templates.router, prefix="/product-cost-templates", tags=["master.product"])
api_router.include_router(product_price_templates.router, prefix="/product-price-templates", tags=["master.product"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["platform.workflow"])
api_router.include_router(audits.router, prefix="/audits", tags=["platform.audit"])
api_router.include_router(configs.router, prefix="/configs", tags=["platform.config"])
api_router.include_router(business_settings.router, prefix="/business-settings", tags=["platform.business-settings"])
api_router.include_router(files.router, prefix="/files", tags=["platform.file"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["business.quote"])
api_router.include_router(projects.router, prefix="/projects", tags=["business.project"])
api_router.include_router(
    project_actual_costs.router,
    prefix="/project-actual-costs",
    tags=["business.actual_cost"],
)
api_router.include_router(
    procurement_entries.router,
    prefix="/procurement-entries",
    tags=["business.procurement"],
)
api_router.include_router(work_orders.router, prefix="/work-orders", tags=["business.work_order"])
api_router.include_router(fieldwork_records.router, prefix="/fieldwork-records", tags=["business.fieldwork"])
api_router.include_router(cost_estimates.router, prefix="/cost-estimates", tags=["business.cost_estimate"])
api_router.include_router(accounting.router, prefix="/accounting", tags=["business.accounting"])
api_router.include_router(approval_hub.router, prefix="/approvals", tags=["business.approval"])
api_router.include_router(workshop.router, prefix="/workshop", tags=["business.workshop"])
api_router.include_router(mes.router, prefix="/mes", tags=["integration.mes"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["platform.notification"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["platform.realtime"])
api_router.include_router(ai.router, prefix="/ai", tags=["platform.ai"])
api_router.include_router(installation_plans.router, prefix="", tags=["master.machine"])
api_router.include_router(acceptance.router, prefix="", tags=["master.machine"])
api_router.include_router(option_groups.router, prefix="", tags=["master.machine"])
api_router.include_router(aftersales.router, prefix="/aftersales", tags=["business.aftersales"])
