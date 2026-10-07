from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class TimestampMixin:
    # Round 228: `AuditSoftDeleteMixin` below indexes both columns its WHERE clause uses (`created_by`, `is_deleted`), and
    # this mixin indexed neither of its own. **`common_repository.paginate_query` orders every paginated list by
    # `created_at DESC`** — twenty-five models' worth of lists — so all of them sorted an unindexed column. The only
    # `created_at` index in the whole migration chain was `ix_realtime_events_created_at`.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )


class AuditSoftDeleteMixin:
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("sys_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )
