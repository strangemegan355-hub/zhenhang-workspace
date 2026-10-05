from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.machine import Machine
from app.models.quote import Quote, QuoteExportTask
from app.repositories import work_order_repository as work_order_repo
from app.services import work_order_service as work_order_svc
from app.services.mes_integration_service import latest_oee_by_line, list_recent_signals


async def get_workshop_board(db: AsyncSession) -> dict:
    now = datetime.now(UTC)
    quote_rows = list(
        (
            await db.execute(
                select(Quote).where(Quote.is_deleted.is_(False)).order_by(Quote.updated_at.desc()).limit(24)
            )
        ).scalars().all()
    )
    machines = list(
        (await db.execute(select(Machine).where(Machine.is_deleted.is_(False)).limit(50))).scalars().all()
    )
    export_pending = int(
        (
            await db.execute(
                select(func.count()).select_from(QuoteExportTask).where(
                    QuoteExportTask.is_deleted.is_(False),
                    QuoteExportTask.status == "pending",
                )
            )
        ).scalar_one()
    )

    by_state: dict[str, int] = {}
    for q in quote_rows:
        by_state[q.workflow_state] = by_state.get(q.workflow_state, 0) + 1

    reviewing = by_state.get("reviewing", 0)
    approved = by_state.get("approved", 0)
    total_active = len(quote_rows) or 1
    oee_availability = round((approved / total_active) * 100, 1)
    oee_performance = round(max(0, 100 - reviewing * 8), 1)
    oee_quality = round(max(0, 100 - export_pending * 5), 1)
    oee = round((oee_availability * oee_performance * oee_quality) / 10000, 3)
    mes_oee = await latest_oee_by_line(db) if settings.mes_enabled else {}
    if mes_oee:
        first = next(iter(mes_oee.values()))
        oee_availability = first.get("availability", oee_availability)
        oee_performance = first.get("performance", oee_performance)
        oee_quality = first.get("quality", oee_quality)
        oee = first.get("oee", oee)

    mes_signals = []
    if settings.mes_enabled:
        for sig in await list_recent_signals(db, limit=20):
            mes_signals.append(
                {
                    "equipment_code": sig.equipment_code,
                    "signal_key": sig.signal_key,
                    "signal_value": float(sig.signal_value),
                    "collected_at": sig.collected_at.isoformat(),
                }
            )

    wo_summary = await work_order_svc.get_summary(db)
    wo_kanban_raw = await work_order_repo.list_kanban(db, limit_per_column=12)
    wo_kanban = {
        key: [work_order_svc.serialize_for_board(item) for item in items]
        for key, items in wo_kanban_raw.items()
    }

    equipment = []
    for m in machines[:12]:
        status = m.status
        if status == "draft":
            status = "idle"
        equipment.append(
            {
                "id": str(m.id),
                "code": m.machine_code,
                "name": m.name,
                "status": status,
                "model_no": m.model_no,
            }
        )

    alarms: list[dict] = []
    if wo_summary.exception_count > 0:
        alarms.append(
            {
                "level": "warning",
                "code": "WORK_ORDER_EXCEPTION",
                "message": f"{wo_summary.exception_count} 张工单存在异常",
                "at": now.isoformat(),
            }
        )
    if reviewing > 0:
        alarms.append(
            {
                "level": "warning",
                "code": "QUOTE_REVIEW_BACKLOG",
                "message": f"{reviewing} 笔报价待审批",
                "at": now.isoformat(),
            }
        )
    if export_pending > 0:
        alarms.append(
            {
                "level": "info",
                "code": "EXPORT_QUEUE",
                "message": f"{export_pending} 个导出任务排队",
                "at": now.isoformat(),
            }
        )
    for q in quote_rows:
        if q.workflow_state == "reviewing" and float(q.total_amount) > 500000:
            alarms.append(
                {
                    "level": "critical",
                    "code": "HIGH_VALUE_REVIEW",
                    "message": f"{q.quote_no} 大额待审 ¥{q.total_amount}",
                    "at": now.isoformat(),
                }
            )
            if len(alarms) >= 8:
                break

    production_lines = [
        {
            "line_id": "L1",
            "name": "装配一线",
            "state": "running" if approved > 0 else "idle",
            "wip_quotes": reviewing,
            "throughput_target": 12,
        },
        {
            "line_id": "L2",
            "name": "调试二线",
            "state": "running" if by_state.get("draft", 0) < 5 else "blocked",
            "wip_quotes": by_state.get("draft", 0),
            "throughput_target": 8,
        },
    ]

    return {
        "generated_at": now.isoformat(),
        "production": {
            "lines": production_lines,
            "quote_pipeline": [{"state": k, "count": v} for k, v in by_state.items()],
        },
        "equipment": equipment,
        "alarms": alarms[:10],
        "oee": {
            "availability": oee_availability,
            "performance": oee_performance,
            "quality": oee_quality,
            "oee": oee,
            "mes_lines": mes_oee,
            "foundation_note": "ERP 推算 + MES 快照；可经 /api/v1/mes 接入实采",
        },
        "mes_signals": mes_signals,
        "work_orders": {
            "summary": wo_summary.model_dump(),
            "kanban": wo_kanban,
        },
        "live_quotes": [
            {
                "id": str(q.id),
                "quote_no": q.quote_no,
                "title": q.title,
                "workflow_state": q.workflow_state,
                "total_amount": str(q.total_amount),
                "updated_at": q.updated_at.isoformat() if q.updated_at else None,
            }
            for q in quote_rows[:16]
        ],
    }
