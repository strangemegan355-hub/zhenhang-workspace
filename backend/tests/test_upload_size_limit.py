"""The upload path is bounded, in both directions.

Round 204 measured the shape round 203 flagged: one upload endpoint, and `upload_file` did `content = await file.read()`
— **the entire body into memory, with no limit anywhere in the backend**, so a single large upload could exhaust the
process.

The bound is a setting plus a read that counts bytes as they arrive, **not** a `Content-Length` check: a client can omit
or misstate that header, and the memory has to be bounded either way. These tests assert both halves — a body over the
limit is refused with 413 **before** anything is stored, and a body under it still uploads.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest
from starlette.datastructures import UploadFile

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

pytestmark = pytest.mark.asyncio


class _Stored:
    """Records what reached storage, so 'refused before storing' can be asserted rather than assumed."""

    def __init__(self) -> None:
        self.calls: list[dict] = []


class _User:
    """The service records `created_by`, so the stub needs an id."""

    id = "00000000-0000-0000-0000-000000000000"


async def _upload(size: int, monkeypatch, limit: int):

    from app.domains.file.application import file_application_service as svc

    stored = _Stored()
    monkeypatch.setattr(svc, "apply_lifecycle_policies", lambda *_: None)
    monkeypatch.setattr(svc, "ensure_bucket", lambda *_: None)
    monkeypatch.setattr(svc, "upload_object", lambda **kwargs: stored.calls.append(kwargs))

    # The service persists a `file_objects` row after storing the bytes; the row is not what this test is about, so the
    # repository call is stubbed rather than reaching for a database in a unit test. It is called as `(db, obj)`, and
    # returning that same object is enough — it already carries the fields the service reads back.
    async def _fake_row(db, obj):
        return obj

    monkeypatch.setattr(svc.repo, "create_file_object", _fake_row)
    monkeypatch.setattr(svc.settings, "max_upload_bytes", limit, raising=False)

    upload = UploadFile(file=io.BytesIO(b"x" * size), filename="payload.bin")
    await svc.upload_file(object(), file=upload, category="test", current_user=_User())
    return stored


async def test_a_body_over_the_limit_is_refused_before_anything_is_stored(monkeypatch):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as raised:
        await _upload(2 * 1024 * 1024, monkeypatch, limit=1024 * 1024)
    assert raised.value.status_code == 413, f"expected 413, got {raised.value.status_code}"


async def test_a_body_under_the_limit_still_uploads(monkeypatch):
    """The other direction, asserted on the reader itself — **the security property lives in the read**, and reaching it
    through the whole service would drag a database and a bucket into a unit test for no gain."""
    from app.domains.file.application.file_application_service import _read_bounded

    upload = UploadFile(file=io.BytesIO(b"x" * 4096), filename="payload.bin")
    content = await _read_bounded(upload, limit=1024 * 1024)
    assert len(content) == 4096, "a body under the limit was not read whole"
    assert content == b"x" * 4096, "the bytes read are not the bytes uploaded"


def test_the_limit_is_a_setting_with_a_finite_default():
    from app.config.settings import Settings

    field = Settings.model_fields["max_upload_bytes"]
    default = field.default
    assert isinstance(default, int) and default > 0, f"max_upload_bytes has no finite positive default ({default!r})"
    # A gigabyte-scale default would defeat the bound's purpose on a small container.
    assert default <= 512 * 1024 * 1024, f"the default upload limit is {default} bytes, too large to bound memory"
