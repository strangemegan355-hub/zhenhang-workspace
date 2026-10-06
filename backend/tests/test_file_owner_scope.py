"""The file domain's own owner convention must hold on the single-file read paths.

`list_file_objects` scopes by `created_by=owner_id`, where `owner_scope_user_id` returns None for ALL scope and
the caller's id otherwise. The single-file lookups did not, so preview and download reached any file in any
department — and the preview route discarded the user as `_` while still reading `getattr(_, "id", None)`, so the
id reached the cache row but never the lookup.

These tests replace the repository with a recorder and use transient ORM objects, so no database or Redis is
involved. A transient `User` needs an explicit `id` because the policy builds a UUID from it (the same detail
round 85 learned), and a transient `Role` in `user.roles` is a plain list, which is what ALL scope needs.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

os.environ.setdefault("SECRET_KEY", "unit-test-secret-key-32-characters")

from app.domains.file.application import file_application_service as files  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.user import User  # noqa: E402


class _Recorder:
    def __init__(self, obj) -> None:
        self.obj = obj
        self.calls = 0

    async def get_file_object(self, db, file_id):
        self.calls += 1
        return self.obj


def _user(scope: str) -> User:
    user = User(id=uuid4(), username=f"scope-{scope}", hashed_password="not-used")
    user.roles = [Role(name=f"scope-{scope}", code=f"scope_{scope}", data_scope=scope)]
    return user


@pytest.mark.asyncio
async def test_a_self_scoped_caller_cannot_reach_someone_elses_file(monkeypatch):
    owner = uuid4()
    other = SimpleNamespace(id=uuid4(), created_by=owner, file_name="secret.pdf", mime_type="application/pdf")
    recorder = _Recorder(other)
    monkeypatch.setattr(files.repo, "get_file_object", recorder.get_file_object)

    with pytest.raises(HTTPException) as raised:
        await files.get_file_or_404(None, other.id, _user("self"))

    assert raised.value.status_code == 404, "an out-of-scope file must be indistinguishable from a missing one"


@pytest.mark.asyncio
async def test_a_self_scoped_caller_reaches_their_own_file(monkeypatch):
    caller = _user("self")
    own = SimpleNamespace(id=uuid4(), created_by=caller.id, file_name="mine.pdf", mime_type="application/pdf")
    recorder = _Recorder(own)
    monkeypatch.setattr(files.repo, "get_file_object", recorder.get_file_object)

    assert await files.get_file_or_404(None, own.id, caller) is own


@pytest.mark.asyncio
async def test_an_all_scoped_caller_reaches_any_file(monkeypatch):
    other = SimpleNamespace(id=uuid4(), created_by=uuid4(), file_name="x.pdf", mime_type="application/pdf")
    recorder = _Recorder(other)
    monkeypatch.setattr(files.repo, "get_file_object", recorder.get_file_object)

    assert await files.get_file_or_404(None, other.id, _user("all")) is other


@pytest.mark.asyncio
async def test_download_goes_through_the_same_check(monkeypatch):
    other = SimpleNamespace(
        id=uuid4(),
        created_by=uuid4(),
        file_name="x.pdf",
        mime_type="application/pdf",
        bucket="erp",
        object_name="x/y.pdf",
    )
    recorder = _Recorder(other)
    monkeypatch.setattr(files.repo, "get_file_object", recorder.get_file_object)

    with pytest.raises(HTTPException) as raised:
        await files.download_file_content(None, other.id, _user("department"))

    assert raised.value.status_code == 404
    assert recorder.calls == 1, "the lookup itself must be the thing that refuses"
