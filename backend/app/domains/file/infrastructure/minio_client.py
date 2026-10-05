"""Object storage access, and the one lifecycle rule this deployment applies.

Object expiration is deliberately **not** configured here, even though the database carries a
`file_lifecycle_policies` table with a 365-day default. Those rows were created automatically on the
first upload of a category and attributed to whoever uploaded that file, and nothing has ever
enforced them. Translating that default into a real MinIO expiry rule would delete customer
contracts, drawings and acceptance photos one year after upload — a decision nobody made and one
that cannot be undone. Retention therefore stays an explicit, unenforced intent until an
administrator chooses it deliberately.
"""

import logging
from io import BytesIO
from datetime import timedelta

from app.config.settings import settings

logger = logging.getLogger(__name__)

#: Interrupted uploads leave orphaned parts behind. They are never a valid object, so removing them
#: costs nothing; the delay only avoids racing an upload that is still in progress.
ABORT_INCOMPLETE_MULTIPART_DAYS = 7


def _client():
    from minio import Minio

    return Minio(
        settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(bucket: str) -> None:
    client = _client()
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)


def upload_object(*, bucket: str, object_name: str, data: bytes, content_type: str | None) -> None:
    client = _client()
    from minio.error import S3Error

    try:
        client.put_object(
            bucket,
            object_name,
            BytesIO(data),
            length=len(data),
            content_type=content_type or "application/octet-stream",
        )
    except S3Error as exc:
        raise RuntimeError(f"MinIO upload failed: {exc.code}") from exc


def presigned_get_url(*, bucket: str, object_name: str, expiry_seconds: int = 3600) -> str:
    client = _client()
    return client.presigned_get_object(bucket, object_name, expires=timedelta(seconds=expiry_seconds))


def get_object_bytes(*, bucket: str, object_name: str) -> bytes:
    client = _client()
    from minio.error import S3Error

    try:
        response = client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as exc:
        raise RuntimeError(f"MinIO download failed: {exc.code}") from exc


def generate_thumbnail_object_name(object_name: str) -> str:
    return f"thumbs/{object_name}"


def build_lifecycle_config():
    """The lifecycle rules for this deployment, as a MinIO LifecycleConfig.

    Exactly one rule: abort incomplete multipart uploads. It is the only one that cannot lose data.
    """
    from minio.lifecycleconfig import AbortIncompleteMultipartUpload, LifecycleConfig, Rule

    return LifecycleConfig(
        [
            Rule(
                status="Enabled",
                rule_id="abort-incomplete-multipart-upload",
                abort_incomplete_multipart_upload=AbortIncompleteMultipartUpload(
                    days_after_initiation=ABORT_INCOMPLETE_MULTIPART_DAYS
                ),
            )
        ]
    )


def apply_lifecycle_policies(bucket: str) -> None:
    """Push the bucket lifecycle rules. Best-effort: storage trouble must not fail an upload."""
    from minio.error import S3Error

    try:
        _client().set_bucket_lifecycle(bucket, build_lifecycle_config())
    except S3Error as exc:
        logger.warning("could not apply lifecycle rules to bucket %s: %s", bucket, exc.code)
    except Exception:  # noqa: BLE001 - a bucket without lifecycle support, or MinIO unreachable
        logger.exception("unexpected failure applying lifecycle rules to bucket %s", bucket)
