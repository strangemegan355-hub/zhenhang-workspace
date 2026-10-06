"""The storage lifecycle against a real MinIO server.

`build_lifecycle_config` is unit-tested against a fake client, which pins *what* the rule says; nothing
had ever pushed it to a real server, so `set_bucket_lifecycle` — and the shape MinIO returns from
`get_bucket_lifecycle` — were unproven. The integration stack now runs MinIO on its own ports
(59000/59001) precisely so this can be checked.

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

# Every lifecycle document is rejected by this server (see the module docstring). The tests that need the
# server to accept one are expected failures, not passes: an XPASS means a client or server change fixed
# it, and the test should then be promoted to a plain assertion.
LIFECYCLE_UNSUPPORTED = pytest.mark.xfail(
    reason=(
        "minio-py 7.2.20 against MinIO RELEASE.2025-09-07 rejects every lifecycle document with "
        "InvalidArgument, including a hand-written spec-shaped one, so the abort-incomplete-multipart-"
        "upload rule this deployment applies has never taken effect"
    ),
    strict=False,
)


def _client():
    """The application's own client, so the test exercises the configured path and not a copy of it."""
    client = minio_client._client()
    if not client.bucket_exists(BUCKET):
        client.make_bucket(BUCKET)
    return client


@LIFECYCLE_UNSUPPORTED
def test_the_lifecycle_rule_round_trips_through_real_minio():
    client = _client()

    minio_client.apply_lifecycle_policies(BUCKET)

    config = client.get_bucket_lifecycle(BUCKET)
    rules = list(config.rules)
    assert len(rules) == 1, f"exactly one rule is intended, MinIO returned {len(rules)}"

    rule = rules[0]
    assert rule.rule_id == "abort-incomplete-multipart-upload"
    assert rule.status == "Enabled"
    assert (
        rule.abort_incomplete_multipart_upload.days_after_initiation
        == minio_client.ABORT_INCOMPLETE_MULTIPART_DAYS
    )


@LIFECYCLE_UNSUPPORTED
def test_the_rule_never_expires_objects():
    """A lifecycle rule that deletes files would be a data-loss bug, so the server's copy is checked."""
    config = _client().get_bucket_lifecycle(BUCKET)
    for rule in config.rules:
        assert getattr(rule, "expiration", None) is None, "the deployment must not expire objects"
        assert getattr(rule, "noncurrent_version_expiration", None) is None


def test_applying_to_a_missing_bucket_does_not_raise():
    """The documented guarantee: storage trouble must not fail an upload."""
    minio_client.apply_lifecycle_policies("definitely-not-a-bucket-in-this-deployment")


@LIFECYCLE_UNSUPPORTED
def test_applying_the_same_policy_twice_is_accepted():
    """The upload path calls this on every upload, so a second application must not be an error."""
    client = _client()
    minio_client.apply_lifecycle_policies(BUCKET)
    minio_client.apply_lifecycle_policies(BUCKET)
    assert len(list(client.get_bucket_lifecycle(BUCKET).rules)) == 1


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-q"]))
