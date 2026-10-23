#!/usr/bin/env python3
"""Rotate the admin password (delivery §4.7). Prints the new password once to stdout.

Usage (API container or local venv with DATABASE_URL):
  python scripts/rotate_admin_password.py
  python scripts/rotate_admin_password.py --password 'explicit-new-password'
"""

from __future__ import annotations

import argparse
import os
import secrets
import string
import sys

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import get_password_hash
from app.models.user import User


def _database_url() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("INTEGRATION_DATABASE_URL")
    if not url:
        from app.config.settings import settings

        url = str(settings.database_url)
    return url.replace("localhost", "127.0.0.1")


def _gen_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default=os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin"))
    parser.add_argument("--password", default="")
    args = parser.parse_args()
    new_password = args.password.strip() or _gen_password()
    if len(new_password) < 12:
        raise SystemExit("password must be at least 12 characters")

    engine = create_engine(_database_url(), pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    with SessionLocal() as db:
        user = db.execute(select(User).where(User.username == args.username)).scalar_one_or_none()
        if user is None:
            raise SystemExit(f"user {args.username!r} not found")
        user.hashed_password = get_password_hash(new_password)
        db.add(user)
        db.commit()
    # Print once for the operator to store in a secrets manager / .env.prod (not committed).
    print(new_password)


if __name__ == "__main__":
    main()
