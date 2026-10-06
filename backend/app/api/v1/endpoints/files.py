from typing import Annotated
from uuid import UUID

from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_permissions
from app.db.session import get_db
from app.domains.file.application import file_application_service as app_svc
from app.models.user import User
from app.schemas.common import PageResponse
from app.schemas.file_center import FileObjectRead, FileRelationCreate, FileRelationRead

router = APIRouter()


@router.post("/upload", response_model=FileObjectRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:file:upload"))],
    category: str = Form(default="general"),
    upload: UploadFile = File(...),
) -> FileObjectRead:
    return await app_svc.upload_file(db, file=upload, category=category, current_user=current)


@router.post("/relations", response_model=FileRelationRead, status_code=status.HTTP_201_CREATED)
async def bind_file_relation(
    payload: FileRelationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:file:bind"))],
) -> FileRelationRead:
    return await app_svc.create_file_relation(db, payload.model_dump(), current)


@router.get("", response_model=PageResponse[FileObjectRead])
async def list_files(
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:file:read"))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    q: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=64),
) -> PageResponse:
    return await app_svc.list_file_objects(
        db,
        page=page,
        page_size=page_size,
        q=q,
        category=category,
        current_user=current,
    )


@router.get("/{file_id}/preview")
async def preview_file(
    file_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:file:read"))],
) -> dict:
    # The user used to be named `_` and only its id reached the preview cache row, never the lookup.
    file_obj = await app_svc.get_file_or_404(db, file_id, current)
    signed = await app_svc.cache_preview_url(db, file_obj.id, current)
    return {
        "preview_url": signed["preview_url"],
        "thumb_url": signed["thumb_url"],
        "cache_hit": signed["cache_hit"],
        "mime_type": file_obj.mime_type,
        "file_name": file_obj.file_name,
    }


@router.get("/{file_id}/download")
async def download_file(
    file_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current: Annotated[User, Depends(require_permissions("platform:file:read"))],
) -> Response:
    data, file_name, mime_type = await app_svc.download_file_content(db, file_id, current)
    safe_name = file_name.replace('"', "")
    encoded = quote(file_name)
    return Response(
        content=data,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{encoded}",
        },
    )
