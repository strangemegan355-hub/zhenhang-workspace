from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIContext, AIDocument, EmbeddingTask


async def prepare_ai_document_from_file(
    db: AsyncSession,
    *,
    file_id,
    title: str,
    biz_type: str,
    biz_id,
    created_by,
) -> None:
    context = AIContext(
        biz_type=biz_type,
        biz_id=biz_id,
        title=f"{title}-context",
        context={"source": "file_upload"},
        metadata_json=None,
        created_by=created_by,
    )
    db.add(context)
    await db.flush()
    document = AIDocument(
        context_id=context.id,
        file_id=file_id,
        title=title,
        content_text=None,
        chunk_count=0,
        status="pending",
        created_by=created_by,
    )
    db.add(document)
    await db.flush()
    task = EmbeddingTask(
        document_id=document.id,
        status="pending",
        retry_count=0,
        dead_letter=False,
        error_message=None,
        created_by=created_by,
    )
    db.add(task)
    await db.flush()
