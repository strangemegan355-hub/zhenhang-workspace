"""Object storage access, and the lifecycle stance this deployment takes.

Object expiration is deliberately **not** configured here, even though the database carries a
`file_lifecycle_policies` table with a 365-day default. Those rows were created automatically on the
first upload of a category and attributed to whoever uploaded that file, and nothing has ever
enforced them. Translating that default into a real MinIO expiry rule would delete customer
contracts, drawings and acceptance photos one year after upload — a decision nobody made and one
that cannot be undone. Retention therefore stays an explicit, unenforced intent until an
administrator chooses it deliberately.

Incomplete multipart cleanup is also **not** applied via PutBucketLifecycle. MinIO rejects
`AbortIncompleteMultipartUpload` rules (minio/minio#16120); the server cleans stale uploads via the
global `api stale_uploads_expiry` setting (default 24h) instead. Calling `set_bucket_lifecycle`
with an abort-only rule therefore never took effect and only produced InvalidArgument noise.
"""

import logging
from datetime import timedelta
from io import BytesIO

from app.config.settings import settings

logger = logging.getLogger(__name__)

#: Historical intent only — MinIO does not honour AbortIncompleteMultipartUpload on buckets.
#: Incomplete multipart parts are purged by the server's `api stale_uploads_expiry` (default 24h).
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
    """Lifecycle rules this deployment would push — intentionally empty.

    MinIO rejects AbortIncompleteMultipartUpload (minio/minio#16120). We also never attach object
    Expiration / Transition rules. Callers that still want a LifecycleConfig object get an empty
    one so unit tests can assert the safety properties without talking to a server.
    """
    from minio.lifecycleconfig import LifecycleConfig

    return LifecycleConfig([])


def apply_lifecycle_policies(bucket: str) -> None:
    """Documented no-op for MinIO: do not push AbortIncomplete or object-expiry rules.

    Best-effort contract preserved: storage lifecycle must never fail an upload. Incomplete
    multipart parts are left to the server's ``api stale_uploads_expiry``.
    """
    logger.info(
        "skipping set_bucket_lifecycle for %s: MinIO rejects AbortIncompleteMultipartUpload "
        "(minio/minio#16120; use api stale_uploads_expiry); object expiry rules are never applied",
        bucket,
    )
