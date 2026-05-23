from uuid import UUID

from app.core.data_scope import DataScope, resolve_data_scope


def owner_scope_user_id(user) -> UUID | None:
    scope = resolve_data_scope(user)
    if scope == DataScope.ALL:
        return None
    return UUID(str(user.id))
