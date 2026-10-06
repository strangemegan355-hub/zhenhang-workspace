"""Re-export of the shared data-scope helper. The implementation lives in `app/core/data_scope.py`.

This module held a byte-identical copy of `owner_scope_user_id` until round 124; it is kept so that
`from app.domains.<name>.policies.data_scope_policy import owner_scope_user_id` keeps resolving.
"""

from app.core.data_scope import owner_scope_user_id

__all__ = ["owner_scope_user_id"]
