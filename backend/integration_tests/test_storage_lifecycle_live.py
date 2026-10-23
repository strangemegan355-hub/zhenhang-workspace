"""The storage lifecycle stance against a real MinIO server.

MinIO rejects AbortIncompleteMultipartUpload in PutBucketLifecycle (minio/minio#16120). This
deployment therefore never pushes a lifecycle document; incomplete multiparts are cleaned by the
server's `api stale_uploads_expiry`. These tests pin that client behaviour and the hard safety
rule: no object-expiration policies are ever applied.

The tests are synchronous on purpose: the MinIO client is blocking, so a loop would add nothing.
"""

from __future__ import annotations

import os

os.environ.setdefault("SECRET_KEY", "integration-secret-key-32-chars-long!")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://erp:erp@localhost:55432/erp_db"
)
os.environ["MINIO_ENDPOINT"] = os.getenv("INTEGRATION_MINIO_ENDPOINT", "127.0.0.1:59000")

import pytest
from app.domains.file.infrastructure import minio_client  # noqa: E402

BUCKET = "erp-files-integration"


def _client():
    """The application's own client, so the test exercises the configured path and not a copy of it."""
    client = minio_client._client()
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)
    return client


def test_apply_lifecycle_does_not_raise_against_real_minio():
    """Documented no-op: must succeed even when AbortIncomplete would have been InvalidArgument."""
    _client()
    minio_client.apply_lifecycle_policies(BUCKET)


def test_apply_never_installs_object_expiration():
    """Safety: whatever lifecycle MinIO already has, we must not add Expiration rules."""
    client = _client()
    minio_client.apply_lifecycle_policies(BUCKET)
    try:
        config = client.get_bucket_lifecycle(BUCKET)
    except Exception as exc:  # noqa: BLE001 - NoSuchLifecycleConfiguration and friends are fine
        # Empty / missing lifecycle is the expected post-align state.
        assert "NoSuch" in type(exc).__name__ or "NoSuch" in str(exc) or "lifecycle" in str(exc).lower()
        return
    if config is None:
        return
    for rule in list(config.rules or []):
        assert getattr(rule, "expiration", None) is None, "the deployment must not expire objects"
        assert getattr(rule, "noncurrent_version_expiration", None) is None


def test_applying_to_a_missing_bucket_does_not_raise():
    """The documented guarantee: storage trouble must not fail an upload."""
    minio_client.apply_lifecycle_policies("definitely-not-a-bucket-in-this-deployment")


def test_applying_the_same_policy_twice_is_accepted():
    """The upload path calls this on every upload, so a second application must not be an error."""
    _client()
    minio_client.apply_lifecycle_policies(BUCKET)
    minio_client.apply_lifecycle_policies(BUCKET)


def test_build_lifecycle_config_stays_empty_even_live():
    """Pin the client contract independently of what the server already stores."""
    assert list(minio_client.build_lifecycle_config().rules) == []


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
