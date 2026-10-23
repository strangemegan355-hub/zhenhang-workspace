from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class AIContext(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "ai_contexts"

    biz_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    biz_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    creator: Mapped[User | None] = relationship(foreign_keys="AIContext.created_by", lazy="joined")


class AIDocument(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "ai_documents"

    context_id: Mapped[UUID] = mapped_column(ForeignKey("ai_contexts.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id: Mapped[UUID | None] = mapped_column(ForeignKey("file_objects.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending", index=True)

    context_ref: Mapped[AIContext] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys="AIDocument.created_by", lazy="joined")


class AIEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "ai_embeddings"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("ai_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    vector: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, default="pending", server_default="pending")
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    document: Mapped[AIDocument] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys="AIEmbedding.created_by", lazy="joined")


class EmbeddingTask(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "embedding_tasks"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("ai_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", server_default="pending", index=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    dead_letter: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[AIDocument] = relationship()
    creator: Mapped[User | None] = relationship(foreign_keys="EmbeddingTask.created_by", lazy="joined")
