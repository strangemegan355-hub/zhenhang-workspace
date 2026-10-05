from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class FileObject(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "file_objects"

    bucket: Mapped[str] = mapped_column(String(64), nullable=False)
    object_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_ext: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general", server_default="general", index=True)
    preview_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    creator: Mapped["User | None"] = relationship(foreign_keys="FileObject.created_by", lazy="joined")
    relations: Mapped[list[FileRelation]] = relationship(back_populates="file")


class FileRelation(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "file_relations"

    file_id: Mapped[UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    biz_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    biz_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False, default="attachment", server_default="attachment")
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    file: Mapped[FileObject] = relationship(back_populates="relations")
    creator: Mapped["User | None"] = relationship(foreign_keys="FileRelation.created_by", lazy="joined")


class FilePreviewCache(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "file_preview_caches"

    file_id: Mapped[UUID] = mapped_column(ForeignKey("file_objects.id", ondelete="CASCADE"), nullable=False, index=True)
    cache_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    preview_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumb_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expires_at: Mapped[str | None] = mapped_column(String(64), nullable=True)

    file: Mapped[FileObject] = relationship()
    creator: Mapped["User | None"] = relationship(foreign_keys="FilePreviewCache.created_by", lazy="joined")


class FileLifecyclePolicy(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    """Retention intent per file category. Nothing enforces it, and no code writes rows.

    The table exists for a retention feature that was never built, and it has no API. Its rows must
    not be created implicitly: a policy means an administrator decided something. Object expiration
    is deliberately absent from the MinIO lifecycle configuration — see
    `app/domains/file/infrastructure/minio_client.py` for why turning `retention_days` into a real
    expiry rule would destroy documents.
    """

    __tablename__ = "file_lifecycle_policies"

    category: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    retention_days: Mapped[int] = mapped_column(nullable=False, default=365, server_default="365")
    archive_after_days: Mapped[int | None] = mapped_column(nullable=True)
    delete_after_days: Mapped[int | None] = mapped_column(nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    creator: Mapped["User | None"] = relationship(foreign_keys="FileLifecyclePolicy.created_by", lazy="joined")
