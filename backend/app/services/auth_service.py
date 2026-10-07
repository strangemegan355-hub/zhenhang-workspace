import asyncio
import logging
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.repositories.user_repository import get_user_by_username

logger = logging.getLogger(__name__)

# Round 223: the failure path used to return early when the username did not exist, **skipping bcrypt — the only expensive
# step** — so a nonexistent username answered far faster than a wrong password. That difference is a username-enumeration
# oracle: it tells an attacker which accounts exist without ever guessing a password.
#
# Verifying against this hash costs the same as verifying against a real one and can never succeed, because nobody holds
# its preimage. It is generated once at import rather than hardcoded, so no repository file contains a usable hash of a
# known value.
_DUMMY_HASH = get_password_hash(secrets.token_urlsafe(32))


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None:
        # Pay the same cost as the wrong-password path below before failing, so the two are indistinguishable by timing.
        await asyncio.to_thread(verify_password, password, _DUMMY_HASH)
        # Round 237: a failed credential check was recorded nowhere — not in a log, not in the audit log — so an operator
        # had no way to notice an attack in progress.
        # **The two paths say which case it was, because the log is read by operators and not by attackers**; the
        # *response* stays identical, which is where round 223's enumeration oracle mattered. **No policy lives here: how
        # many failures are too many is a decision, and this is only the record that they happened.**
        logger.warning("Failed login for username=%r (no such account)", username)
        return None
    valid = await asyncio.to_thread(verify_password, password, user.hashed_password)
    if not valid:
        logger.warning("Failed login for username=%r (bad password)", username)
        return None
    return user
