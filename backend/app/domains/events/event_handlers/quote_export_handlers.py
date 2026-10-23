from datetime import UTC, datetime
from time import perf_counter
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enterprise_metrics import enterprise_metrics
from app.domains.quote.application.quote_export_payload import build_export_payload
from app.notifications.notification_service import create_notification
from app.realtime.publish import push_quote_export_status
from app.services.quote_template_engine import render_document


async def handle_quote_export_requested(db: AsyncSession, payload: dict) -> None:
    from app.domains.file.application.file_application_service import store_generated_file
    from app.domains.quote.application.quote_application_service import (
        complete_export_task,
        get_export_task,
    )

    task_id = UUID(str(payload["task_id"]))
    task = await get_export_task(db, task_id)
    if task is None:
        return

    export_started = perf_counter()
    export_format = str(payload.get("format") or task.format)
    template_id = payload.get("template_id")
    doc_payload = await build_export_payload(
        db,
        task.quote_id,
        export_format=export_format,
        template_id=str(template_id) if template_id else None,
    )
    data, ext = render_document(doc_payload, template_id=doc_payload.get("template_id"))
    # Include a fresh suffix so re-processing / retry never collides with ix_file_objects_object_name.
    object_name = f"exports/quotes/{task.quote_id}-{task.id}-{uuid4().hex[:8]}.{ext}"
    mime_type = (
        "application/pdf"
        if ext == "pdf"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    file_obj = await store_generated_file(
        db,
        object_name=object_name,
        file_name=f"{doc_payload.get('quote_no', task.quote_id)}.{ext}",
        file_ext=ext,
        mime_type=mime_type,
        data=data,
        created_by=UUID(str(payload["created_by"])) if payload.get("created_by") else None,
    )
    await complete_export_task(db, task, file_id=file_obj.id)
    task.completed_at = datetime.now(UTC)
    enterprise_metrics.record_export(duration_ms=(perf_counter() - export_started) * 1000, failed=False)
    # No quote read here: `build_export_payload` already returned the quote number, and reading the quote again
    # would be a second unscoped read of a scoped row for a notification string.
    quote_no = str(doc_payload.get("quote_no") or task.quote_id)
    receiver_id = UUID(str(payload["created_by"])) if payload.get("created_by") else task.created_by
    owner_id = doc_payload.get("created_by")
    owner_uuid = UUID(str(owner_id)) if owner_id else receiver_id
    if receiver_id:
        await create_notification(
            db,
            title="报价导出完成",
            content=f"报价 {quote_no} 的 {ext.upper()} 导出已完成，可下载。",
            biz_type="quote_export",
            biz_id=task.id,
            receiver_id=receiver_id,
            payload={"file_id": str(file_obj.id), "format": ext, "template_id": template_id},
            created_by=receiver_id,
            autocommit=False,
        )
        await push_quote_export_status(
            user_id=receiver_id,
            task_id=task.id,
            quote_id=task.quote_id,
            quote_no=quote_no,
            status="completed",
            file_id=file_obj.id,
            owner_id=owner_uuid,
        )
