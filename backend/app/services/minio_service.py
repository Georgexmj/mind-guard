from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from minio import Minio

from app.config import settings


def _build_client() -> Minio:
    client = Minio(
        endpoint=settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE,
    )
    bucket_name = settings.MINIO_BUCKET
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
    return client


def upload_bytes(
    *,
    file_bytes: bytes,
    filename: str,
    prefix: str,
    content_type: str,
) -> str:
    if not file_bytes:
        raise ValueError("file_bytes is empty")

    client = _build_client()
    safe_name = Path(filename or "upload.bin").name
    ext = Path(safe_name).suffix or ".bin"
    object_name = (
        f"{prefix.strip('/')}/"
        f"{datetime.utcnow().strftime('%Y%m%d')}/"
        f"{uuid4().hex}{ext}"
    )

    from io import BytesIO

    stream = BytesIO(file_bytes)
    client.put_object(
        bucket_name=settings.MINIO_BUCKET,
        object_name=object_name,
        data=stream,
        length=len(file_bytes),
        content_type=content_type or "application/octet-stream",
    )
    return object_name


def build_object_url(object_name: str) -> str:
    scheme = "https" if settings.MINIO_SECURE else "http"
    return f"{scheme}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"

