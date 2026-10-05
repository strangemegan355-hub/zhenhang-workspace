"""The storage lifecycle must apply exactly one rule, and it must not be an expiry.

The dangerous version of "finishing the placeholder" is to sync `file_lifecycle_policies` rows into
MinIO expiry rules: those rows were auto-created on first upload with a 365-day default attributed
to the uploader, so it would delete customer documents a year later. These tests pin the safe
behaviour, and they need neither MinIO nor a database.

`SECRET_KEY` is set before importing application modules, as elsewhere in this suite.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SECRET_KEY", "0123456789012345678901234567890123")


def test_lifecycle_applies_only_the_safe_rule():
    from app.domains.file.infrastructure.minio_client import build_lifecycle_config

    config = build_lifecycle_config()
    rules = config.rules
    assert len(rules) == 1, "only one lifecycle rule is intended"

    rule = rules[0]
    assert rule.abort_incomplete_multipart_upload is not None, "the abort rule is the whole point"
    assert rule.abort_incomplete_multipart_upload.days_after_initiation >= 1


def test_lifecycle_sets_no_expiration():
    """The guard rail: no rule may expire objects, whatever the database says."""
    from app.domains.file.infrastructure.minio_client import build_lifecycle_config

    for rule in build_lifecycle_config().rules:
        assert rule.expiration is None, "an expiry rule would delete business documents"
        assert rule.noncurrent_version_expiration is None
        assert rule.transition is None
        assert rule.noncurrent_version_transition is None


def test_a_storage_failure_does_not_propagate(monkeypatch):
    from app.domains.file.infrastructure import minio_client

    class BrokenClient:
        def set_bucket_lifecycle(self, bucket, config):  # noqa: ANN001, ANN201
            from minio.error import S3Error

            raise S3Error(
                code="NotImplemented",
                message="lifecycle not supported",
                resource=bucket,
                request_id="t",
                host_id="t",
                response=None,
            )

    monkeypatch.setattr(minio_client, "_client", lambda: BrokenClient())
    # Best-effort: an upload must not fail because the bucket cannot hold lifecycle rules.
    minio_client.apply_lifecycle_policies("erp")


def test_uploads_do_not_fabricate_a_retention_policy():
    """A policy row must mean an administrator decided something, so no upload may create one."""
    source = open(
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "app",
            "domains",
            "file",
            "application",
            "file_application_service.py",
        ),
        encoding="utf-8",
    ).read()
    assert "ensure_lifecycle_policy" not in source
    assert "create_lifecycle_policy" not in source


def test_the_repository_no_longer_exposes_policy_writes():
    from app.domains.file.repositories import file_repository as repo

    assert not hasattr(repo, "create_lifecycle_policy")
    assert not hasattr(repo, "get_lifecycle_policy_by_category")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
