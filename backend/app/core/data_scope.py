from enum import StrEnum
from uuid import UUID

from sqlalchemy import false


class DataScope(StrEnum):
    ALL = "all"
    SELF = "self"
    DEPARTMENT = "department"
    NONE = "none"


def resolve_data_scope(user) -> DataScope:
    if getattr(user, "is_superuser", False):
        return DataScope.ALL
    role_scopes = {getattr(role, "data_scope", DataScope.SELF) for role in getattr(user, "roles", [])}
    if DataScope.ALL in role_scopes:
        return DataScope.ALL
    if DataScope.DEPARTMENT in role_scopes:
        return DataScope.DEPARTMENT
    if DataScope.SELF in role_scopes:
        return DataScope.SELF
    return DataScope.SELF


def build_created_by_filter(model, user) -> object:
    scope = resolve_data_scope(user)
    if scope == DataScope.ALL:
        return model.is_deleted.is_(False)
    if scope == DataScope.SELF:
        return (model.is_deleted.is_(False)) & (model.created_by == UUID(str(user.id)))
    if scope == DataScope.DEPARTMENT:
        # Placeholder for department-based joins, to be expanded in next phase.
        return model.is_deleted.is_(False)
    return false()
