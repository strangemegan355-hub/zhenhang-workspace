from enum import StrEnum
from uuid import UUID

from sqlalchemy import Select, false, select, true


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


def owner_scope_user_id(user) -> UUID | None:
    """The user id a repository filters on for SELF scope, or None when the scope is ALL.

    This lived as three byte-identical copies under `app/domains/{config,file,quote}/policies/` until round 124.
    The `scope_predicate` docstring above names that helper as one half of the historical contradiction — two
    implementations of one enum with contradictory meanings — so a second copy of it is precisely how that
    contradiction can return: a fix applied in three places is a fix that can diverge three ways.
    """
    scope = resolve_data_scope(user)
    if scope == DataScope.ALL:
        return None
    return UUID(str(user.id))


def _own_rows(model, user):
    return model.created_by == UUID(str(user.id))


def scope_predicate(model, user):
    """The one predicate that restricts `model` rows to a user's data scope.

    This is the single source of truth for a four-valued enum that previously had two
    implementations with contradictory meanings:

      * `build_created_by_filter` treated DEPARTMENT as unrestricted, so a department-scoped
        role could read every department's rows;
      * the `owner_scope_user_id` helper duplicated in the domain policies treated DEPARTMENT as
        SELF, so the same role could read only the rows it had created itself.

    Which behaviour a caller got depended only on which module answered the request. Department
    scope is expressed as a subquery over the users table, so no business table needs a new
    column for it. `model` must expose `created_by`, which every model built on
    AuditSoftDeleteMixin does.
    """
    scope = resolve_data_scope(user)
    if scope == DataScope.ALL:
        return true()
    if scope == DataScope.SELF:
        return _own_rows(model, user)
    if scope == DataScope.DEPARTMENT:
        # Imported lazily: this module sits below the model layer, and importing the user model
        # at module scope would invert that dependency for every importer of data_scope.
        from app.models.user import User

        department_id = getattr(user, "department_id", None)
        if department_id is None:
            # An account with no department cannot be scoped to one. The narrowest safe reading
            # of "department" is then "my own rows", never "everything".
            return _own_rows(model, user)
        return model.created_by.in_(select(User.id).where(User.department_id == department_id))
    return false()


def apply_data_scope(stmt: Select, model, user) -> Select:
    """Restrict an existing statement to the caller's data scope."""
    return stmt.where(scope_predicate(model, user))


def scope_predicate_via_parent(child_model, parent_model, foreign_key, user):
    """Scope rows whose visibility follows the parent row's owner.

    A project actual cost belongs to a project. Scoping it by its own creator would hide part of a
    project the caller is allowed to see — a narrower answer than the one the caller is entitled
    to — so the predicate delegates: the child is visible exactly when its parent is.
    """
    return foreign_key.in_(select(parent_model.id).where(scope_predicate(parent_model, user)))


def build_created_by_filter(model, user) -> object:
    """Backward-compatible wrapper: the soft-delete filter plus the scope predicate.

    Kept for the audit list, which relied on this name. New code should call `scope_predicate`
    (to embed the predicate in a statement it is building) or `apply_data_scope`.
    """
    return model.is_deleted.is_(False) & scope_predicate(model, user)
