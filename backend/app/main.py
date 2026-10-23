import asyncio
import json
import sys
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.v1.router import api_router
from app.config.settings import settings
from app.core.enterprise_metrics import enterprise_metrics
from app.core.exceptions import BusinessException
from app.core.monitoring import now_perf
from app.core.redis_client import close_redis
from app.core.response import error_response, success_response
from app.db.session import dispose_engine
from app.domains.events.application.register_handlers import register_default_event_handlers


@asynccontextmanager
async def lifespan(_: FastAPI):
    register_default_event_handlers()
    try:
        yield
    finally:
        await close_redis()
        await dispose_engine()


openapi_tags = [
    {"name": "system.health", "description": "Service health and readiness probes"},
    {"name": "system.auth", "description": "Authentication and token management"},
    {"name": "system.user", "description": "User and profile APIs"},
    {"name": "master.customer", "description": "Customer master data"},
    {"name": "master.machine", "description": "Machine master and standards"},
    {"name": "master.bom", "description": "BOM and cost management"},
    {"name": "platform.workflow", "description": "Workflow state engine"},
    {"name": "platform.audit", "description": "Audit log queries"},
    {"name": "platform.config", "description": "System configuration center"},
    {"name": "platform.file", "description": "File center and attachments"},
    {"name": "platform.event", "description": "Event bus operations"},
    {"name": "platform.notification", "description": "Notification center"},
    {"name": "platform.realtime", "description": "SSE/WebSocket stream with cursor replay and ACL"},
    {"name": "business.workshop", "description": "Workshop live board and OEE foundation"},
    {"name": "integration.mes", "description": "MES equipment signals and OEE snapshots"},
    {"name": "business.quote", "description": "Quote domain APIs"},
]

_is_production = settings.environment == "production" or settings.app_env == "prod"

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)


class UnifiedResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = now_perf()
        response = await call_next(request)
        elapsed_ms = (now_perf() - started) * 1000
        enterprise_metrics.mark_request(elapsed_ms=elapsed_ms, status_code=response.status_code)

        if request.method == "OPTIONS":
            return response
        if not request.url.path.startswith(settings.api_v1_prefix):
            return response
        if request.url.path in {"/docs", "/redoc", "/openapi.json"}:
            return response
        if response.headers.get("content-type", "").startswith("text/event-stream"):
            return response

        if request.url.path.rstrip("/").endswith("/download"):
            return response
        if response.headers.get("content-disposition"):
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        if not body:
            wrapped = success_response(None)
        else:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=response.status_code,
                    content=success_response(body.decode("utf-8", errors="ignore")),
                )
            if isinstance(payload, dict) and {"code", "message", "data"}.issubset(payload.keys()):
                wrapped = payload
            elif response.status_code >= 400:
                wrapped = error_response(message="Request failed", code="HTTP_ERROR", detail=payload)
            else:
                wrapped = success_response(payload)
        return JSONResponse(status_code=response.status_code, content=wrapped)


app.add_middleware(UnifiedResponseMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(BusinessException)
async def business_exception_handler(_: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.message, code=exc.code),
    )


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    payload: dict[str, str] = {"service": settings.app_name, "version": __version__}
    if not _is_production:
        payload["docs"] = "/docs"
    return payload
