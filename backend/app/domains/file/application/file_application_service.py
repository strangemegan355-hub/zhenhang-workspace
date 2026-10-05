from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ai_preparation_service import prepare_ai_document_from_file
from app.config.settings import settings
from app.core.redis_client import get_redis
from app.domains.events.application.event_bus import event_bus
from app.domains.file.infrastructure.minio_client import (
    apply_lifecycle_policies,
    ensure_bucket,
    generate_thumbnail_object_name,
    get_object_bytes,
    presigned_get_url,
    upload_object,
)
from app.domains.file.policies.data_scope_policy import owner_scope_user_id
from app.domains.file.repositories import file_repository as repo
from app.schemas.common import PageResponse
from app.services.audit_service import write_audit_log


async def upload_file(
    db: AsyncSession,
    *,
    file: UploadFile,
    category: str,
    current_user,
) -> object:
    # Apply the bucket lifecycle rules (abort incomplete multipart uploads). No retention row is
    # created: a `file_lifecycle_policies` row should mean an administrator decided something, and
    # nothing enforces those rows, so silently writing a 365-day default would be a false record.
    apply_lifecycle_policies(settings.minio_bucket)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    suffix = Path(file.filename or "unknown").suffix.lower()
    object_name = f"{category}/{uuid4().hex}{suffix}"
    ensure_bucket(settings.minio_bucket)
    upload_object(
        bucket=settings.minio_bucket,
        object_name=object_name,
        data=content,
        content_type=file.content_type,
    )
    thumb_object_name = None
    if (file.content_type or "").startswith("image/"):
        thumb_object_name = generate_thumbnail_object_name(object_name)
        upload_object(
            bucket=settings.minio_bucket,
            object_name=thumb_object_name,
            data=content,
            content_type=file.content_type,
        )
    obj = await repo.create_file_object(
        db,
        {
            "bucket": settings.minio_bucket,
            "object_name": object_name,
            "file_name": file.filename or object_name,
            "file_ext": suffix.lstrip(".") or None,
            "mime_type": file.content_type,
            "size_bytes": len(content),
            "category": category,
            "preview_url": None,
            "checksum": sha256(content).hexdigest(),
            "created_by": current_user.id,
        },
        autocommit=False,
    )
    obj.preview_url = f"/api/v1/files/{obj.id}/preview"
    await write_audit_log(
        db,
        module="file_center",
        action="upload",
        resource_type="file_object",
        resource_id=obj.id,
        created_by=current_user.id,
        payload={"category": category, "object_name": object_name},
        autocommit=False,
    )
    await event_bus.publish(
        db,
        event_type="file.uploaded",
        aggregate_type="file_object",
        aggregate_id=obj.id,
        payload={"file_id": obj.id, "category": obj.category, "created_by": current_user.id},
        created_by=current_user.id,
    )
    await prepare_ai_document_from_file(
        db,
        file_id=obj.id,
        title=obj.file_name,
        biz_type="file_object",
        biz_id=obj.id,
        created_by=current_user.id,
    )
    await db.commit()
    await db.refresh(obj)
    if thumb_object_name:
        await cache_preview_url(db, obj.id, current_user.id)
    return obj


async def create_file_relation(db: AsyncSession, payload: dict, current_user):
    payload["created_by"] = current_user.id
    relation = await repo.create_file_relation(db, payload, autocommit=False)
    await write_audit_log(
        db,
        module="file_center",
        action="bind",
        resource_type="file_relation",
        resource_id=relation.id,
        created_by=current_user.id,
        payload=payload,
        autocommit=False,
    )
    await db.commit()
    await db.refresh(relation)
    return relation


async def list_file_objects(db: AsyncSession, *, page: int, page_size: int, q: str | None, category: str | None, current_user):
    owner_id = owner_scope_user_id(current_user)
    total, items = await repo.list_file_objects(
        db,
        page=page,
        page_size=page_size,
        q=q,
        category=category,
        created_by=owner_id,
    )
    return PageResponse(total=total, page=page, page_size=page_size, items=items)


async def get_file_or_404(db: AsyncSession, file_id: UUID):
    obj = await repo.get_file_object(db, file_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return obj


async def cache_preview_url(db: AsyncSession, file_id: UUID, current_user_id: UUID | None) -> dict:
    file_obj = await get_file_or_404(db, file_id)
    cache_key = f"file:preview:{file_obj.id}"
    redis = await get_redis()
    cached = await redis.get(cache_key)
    if cached:
        return {"preview_url": cached, "thumb_url": None, "cache_hit": True}
    preview_url = presigned_get_url(bucket=file_obj.bucket, object_name=file_obj.object_name, expiry_seconds=3600)
    thumb_url = None
    if (file_obj.mime_type or "").startswith("image/"):
        thumb_url = presigned_get_url(
            bucket=file_obj.bucket,
            object_name=generate_thumbnail_object_name(file_obj.object_name),
            expiry_seconds=3600,
        )
    await redis.setex(cache_key, 3600, preview_url)
    exists = await repo.get_preview_cache(db, cache_key)
    if exists is None:
        await repo.create_preview_cache(
            db,
            {
                "file_id": file_obj.id,
                "cache_key": cache_key,
                "preview_url": preview_url,
                "thumb_url": thumb_url,
                "expires_at": "3600",
                "created_by": current_user_id,
            },
            autocommit=False,
        )
        await db.commit()
    return {"preview_url": preview_url, "thumb_url": thumb_url, "cache_hit": False}


async def download_file_content(db: AsyncSession, file_id: UUID) -> tuple[bytes, str, str]:
    file_obj = await get_file_or_404(db, file_id)
    data = get_object_bytes(bucket=file_obj.bucket, object_name=file_obj.object_name)
    return data, file_obj.file_name, file_obj.mime_type or "application/octet-stream"

