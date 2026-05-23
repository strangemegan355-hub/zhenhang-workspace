from io import BytesIO
from datetime import timedelta

from app.config.settings import settings


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


def generate_thumbnail_object_name(object_name: str) -> str:
    return f"thumbs/{object_name}"


def apply_lifecycle_policies(bucket: str) -> None:
    # Placeholder: lifecycle rules can be synced from DB policies to MinIO bucket policy.
    # Keep function for platform scheduler/cron integration.
    _ = bucket
