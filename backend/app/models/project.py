from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import AuditSoftDeleteMixin, Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.quote import Quote
    from app.models.user import User


class Project(UUIDPrimaryKeyMixin, TimestampMixin, AuditSoftDeleteMixin, Base):
    __tablename__ = "projects"

    project_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    customer_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    stage: Mapped[str] = mapped_column(String(32), nullable=False, default="lead", server_default="lead", index=True)
    owner_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_quote_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quotes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")

    customer: Mapped["Customer | None"] = relationship(lazy="joined")
    primary_quote: Mapped["Quote | None"] = relationship(foreign_keys=[primary_quote_id], lazy="joined")
    creator: Mapped["User | None"] = relationship(foreign_keys="Project.created_by", lazy="joined")
