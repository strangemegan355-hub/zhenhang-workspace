from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.models.machine import Machine
from app.models.quote import Quote, QuoteExportTask
from app.repositories import work_order_repository as work_order_repo
from app.services import work_order_service as work_order_svc
from app.services.mes_integration_service import latest_oee_by_line, list_recent_signals


def _estimate_oee(*, approved: int, reviewing: int, export_pending: int, total_active: int) -> dict:
    """Fallback used only when no MES snapshot exists, and it is not a measurement.

    Availability is the share of recent quotes already approved; performance and quality are
    penalties per pending review and per queued export. The result is in percentages so the entire
    payload has one scale, and every caller must label it as an estimate.
    """
    availability = round((approved / total_active) * 100, 1)
    performance = round(max(0, 100 - reviewing * 8), 1)
    quality = round(max(0, 100 - export_pending * 5), 1)
    return {
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": round((availability * performance * quality) / 10000, 3),
    }


def _average_mes_oee(mes_oee: dict[str, dict]) -> dict | None:
    """Average the components of the latest snapshot per line and recompute OEE from them.

    Averaging the components rather than the OEE values keeps the three factors consistent with the
    headline number. It is an unweighted average across lines: the snapshot table stores no output
    quantity, so a production-weighted figure is not derivable from it, and the note says so.
    """
    if not mes_oee:
        return None
    lines = list(mes_oee.values())
    availability = round(sum(float(line.get("availability", 0)) for line in lines) / len(lines), 1)
    performance = round(sum(float(line.get("performance", 0)) for line in lines) / len(lines), 1)
    quality = round(sum(float(line.get("quality", 0)) for line in lines) / len(lines), 1)
    return {
        "availability": availability,
        "performance": performance,
        "quality": quality,
        "oee": round((availability * performance * quality) / 10000, 3),
        "line_count": len(lines),
    }


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

    # A stored snapshot is real data, so it is used whenever one exists; `settings.mes_enabled`
    # governs the raw signal list below, not the truth of a measurement already in the table.
    mes_oee = await latest_oee_by_line(db)
    mes_summary = _average_mes_oee(mes_oee)
    if mes_summary is not None:
        oee_values = {key: mes_summary[key] for key in ("availability", "performance", "quality", "oee")}
        mes_line_count = int(mes_summary["line_count"])
        oee_source = "mes"
    else:
        oee_values = _estimate_oee(
            approved=approved,
            reviewing=reviewing,
            export_pending=export_pending,
            total_active=total_active,
        )
        mes_line_count = 0
        oee_source = "estimated"

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
            "availability": oee_values["availability"],
            "performance": oee_values["performance"],
            "quality": oee_values["quality"],
            "oee": oee_values["oee"],
            # One scale for the whole payload: percentages, 0-100. Displays must not rescale it.
            "unit": "percent",
            # "mes" means a stored snapshot; "estimated" means derived from quote state and
            # therefore not usable as an OEE indicator.
            "source": oee_source,
            "mes_line_count": mes_line_count,
            "mes_lines": mes_oee,
            "note": (
                f"MES 实测快照，{mes_line_count} 条产线未加权平均"
                if oee_source == "mes"
                else "无 MES 快照：按报价状态推算的估算值，不可用作 OEE 指标"
            ),
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
