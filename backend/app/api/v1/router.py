from fastapi import APIRouter

from app.api.v1.endpoints import (
    ai,
    audits,
    auth,
    boms,
    configs,
    customers,
    dashboard,
    files,
    health,
    machines,
    mes,
    notifications,
    realtime,
    quotes,
    users,
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
api_router.include_router(boms.router, prefix="/boms", tags=["master.bom"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["platform.workflow"])
api_router.include_router(audits.router, prefix="/audits", tags=["platform.audit"])
api_router.include_router(configs.router, prefix="/configs", tags=["platform.config"])
api_router.include_router(files.router, prefix="/files", tags=["platform.file"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["business.quote"])
api_router.include_router(workshop.router, prefix="/workshop", tags=["business.workshop"])
api_router.include_router(mes.router, prefix="/mes", tags=["integration.mes"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["platform.notification"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["platform.realtime"])
api_router.include_router(ai.router, prefix="/ai", tags=["platform.ai"])
