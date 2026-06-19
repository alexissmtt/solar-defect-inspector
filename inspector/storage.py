"""Object storage for the batch ingestion pipeline.

`LocalObjectStore` reads a directory; `GCSObjectStore` reads a Google Cloud
Storage bucket. Both satisfy the same `ObjectStore` interface, so the pipeline
does not care where images come from -- which is the point of "data integration
from diverse sources".
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Protocol

_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class ObjectStore(Protocol):
    def list_keys(self) -> List[str]: ...

    def read(self, key: str) -> bytes: ...


class LocalObjectStore:
    def __init__(self, root: str):
        self.root = Path(root)

    def list_keys(self) -> List[str]:
        if not self.root.exists():
            return []
        return sorted(
            p.name for p in self.root.iterdir() if p.suffix.lower() in _IMAGE_SUFFIXES
        )

    def read(self, key: str) -> bytes:
        resolved = (self.root / key).resolve()
        if not resolved.is_relative_to(self.root.resolve()):
            raise ValueError(f"Key {key!r} escapes the storage root")
        return resolved.read_bytes()


class GCSObjectStore:
    def __init__(self, bucket: str, prefix: str = ""):
        from google.cloud import storage

        self._client = storage.Client()
        self._bucket_name = bucket
        self._prefix = prefix

    def list_keys(self) -> List[str]:
        blobs = self._client.list_blobs(self._bucket_name, prefix=self._prefix)
        return [b.name for b in blobs if Path(b.name).suffix.lower() in _IMAGE_SUFFIXES]

    def read(self, key: str) -> bytes:
        return self._client.bucket(self._bucket_name).blob(key).download_as_bytes()


def build_store(settings) -> ObjectStore:
    if settings.storage_backend == "gcs":
        if not settings.gcs_bucket:
            raise ValueError("storage_backend=gcs requires INSPECTOR_GCS_BUCKET")
        return GCSObjectStore(settings.gcs_bucket, settings.gcs_prefix)
    return LocalObjectStore(settings.storage_root)
