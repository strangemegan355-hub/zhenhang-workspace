"""The storage lifecycle must never expire objects, and must not pretend MinIO accepts abort rules.

MinIO rejects `AbortIncompleteMultipartUpload` in PutBucketLifecycle (minio/minio#16120); incomplete
multipart cleanup is server-side (`api stale_uploads_expiry`). These tests pin the safe client
stance without needing MinIO or a database.

`SECRET_KEY` is set before importing application modules, as elsewhere in this suite.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")


def test_lifecycle_config_has_no_rules():
    from app.domains.file.infrastructure.minio_client import build_lifecycle_config

    config = build_lifecycle_config()
    assert list(config.rules) == [], "MinIO abort rule is unsupported; config must stay empty"


def test_lifecycle_sets_no_expiration():
    """The guard rail: no rule may expire objects, whatever the database says."""
    from app.domains.file.infrastructure.minio_client import build_lifecycle_config

    for rule in build_lifecycle_config().rules:
        assert rule.expiration is None, "an expiry rule would delete business documents"
        assert rule.noncurrent_version_expiration is None
        assert rule.transition is None
        assert rule.noncurrent_version_transition is None


def test_apply_lifecycle_is_a_documented_noop(monkeypatch):
    """apply_lifecycle_policies must not call set_bucket_lifecycle (abort rule is rejected)."""
    from app.domains.file.infrastructure import minio_client

    class TrackingClient:
        def __init__(self) -> None:
            self.calls = 0

        def set_bucket_lifecycle(self, bucket, config):  # noqa: ANN001, ANN201
            self.calls += 1

    client = TrackingClient()
    monkeypatch.setattr(minio_client, "_client", lambda: client)
    minio_client.apply_lifecycle_policies("erp")
    assert client.calls == 0, "must not push lifecycle docs MinIO will reject"


def test_a_storage_failure_does_not_propagate(monkeypatch):
    from app.domains.file.infrastructure import minio_client

    class BrokenClient:
        def set_bucket_lifecycle(self, bucket, config):  # noqa: ANN001, ANN201
            raise RuntimeError("should never be called")

    monkeypatch.setattr(minio_client, "_client", lambda: BrokenClient())
    # Best-effort: an upload must not fail because lifecycle is a no-op / unsupported.
    minio_client.apply_lifecycle_policies("erp")


def test_uploads_do_not_fabricate_a_retention_policy():
    """A policy row must mean an administrator decided something, so no upload may create one."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "app",
        "domains",
        "file",
        "application",
        "file_application_service.py",
    )
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    assert "ensure_lifecycle_policy" not in source
    assert "create_lifecycle_policy" not in source


def test_the_repository_no_longer_exposes_policy_writes():
    from app.domains.file.repositories import file_repository as repo

    assert not hasattr(repo, "create_lifecycle_policy")
    assert not hasattr(repo, "get_lifecycle_policy_by_category")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
