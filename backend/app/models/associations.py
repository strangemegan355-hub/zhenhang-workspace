from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

user_role_association = Table(
    "sys_user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("sys_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permission_association = Table(
    "sys_role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("sys_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
