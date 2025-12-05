from __future__ import annotations

import io
from typing import Generator, Optional

from azure.core.exceptions import AzureError, ResourceExistsError, ResourceNotFoundError  # type: ignore
from azure.core.pipeline.policies import RetryPolicy  # type: ignore
from azure.storage.blob import (  # type: ignore
    BlobClient,
    BlobServiceClient,
    ContainerClient,
    ContentSettings,
)
from src.core.config import settings


class AzureBlobError(Exception):
    """Base error raised by AzureBlobService."""


class BlobNotFoundError(AzureBlobError):
    """Raised when a requested blob was not found."""


class ContainerNotFoundError(AzureBlobError):
    """Raised when a requested container was not found."""


class BlobAlreadyExistsError(AzureBlobError):
    """Raised when attempting to create a blob that already exists and overwrite is False."""


def _map_azure_error(exc: AzureError) -> AzureBlobError:
    """Map Azure exceptions to our internal error types."""
    # Many azure exceptions include .status_code and .error_code attributes
    status = getattr(exc, "status_code", None)
    code = getattr(exc, "error_code", None)

    if isinstance(exc, ResourceNotFoundError) or status == 404:
        # Azure may raise for missing container or blob – callers typically know what they asked for
        # We default to BlobNotFound; container-specific APIs can override if needed
        return BlobNotFoundError(str(exc))
    if isinstance(exc, ResourceExistsError) or status == 409:
        return BlobAlreadyExistsError(str(exc))
    # Generic
    return AzureBlobError(f"{code or 'AzureError'}: {exc}")


class AzureBlobService:
    """Azure Blob service wrapper providing list, download, and upload helpers with retries/timeouts."""

    def __init__(self, connection_string: Optional[str] = None) -> None:
        self._conn_str = connection_string or settings.AZURE_STORAGE_CONNECTION_STRING
        if not self._conn_str:
            raise AzureBlobError(
                "AZURE_STORAGE_CONNECTION_STRING is not configured. "
                "Set it via environment or .env (do not hard-code)."
            )

        # Configure retry policy using settings
        retry_policy = RetryPolicy(
            retry_total=settings.BLOB_MAX_RETRIES,
            retry_connect=settings.BLOB_MAX_RETRIES,
            retry_read=settings.BLOB_MAX_RETRIES,
            retry_status=settings.BLOB_MAX_RETRIES,
        )
        # Build service client
        self._service: BlobServiceClient = BlobServiceClient.from_connection_string(
            self._conn_str, retry_policy=retry_policy
        )
        self._timeout = settings.BLOB_REQUEST_TIMEOUT_SECS

    def _container_client(self, container: str) -> ContainerClient:
        return self._service.get_container_client(container)

    def _blob_client(self, container: str, blob_name: str) -> BlobClient:
        return self._service.get_blob_client(container=container, blob=blob_name)

    # PUBLIC_INTERFACE
    def list_blobs(self, container: str, prefix: Optional[str] = None) -> Generator[str, None, None]:
        """List blob names in a container under an optional prefix."""
        try:
            client = self._container_client(container)
            # Returns an iterable of BlobProperties
            blobs = client.list_blobs(name_starts_with=prefix, timeout=self._timeout)
            for b in blobs:
                yield b.name
        except AzureError as exc:
            mapped = _map_azure_error(exc)
            # If the container doesn't exist, make error explicit
            if isinstance(exc, ResourceNotFoundError):
                raise ContainerNotFoundError(str(exc)) from exc
            raise mapped from exc

    # PUBLIC_INTERFACE
    def download_text(self, container: str, blob_name: str, encoding: str = "utf-8") -> str:
        """Download a blob as text."""
        try:
            blob = self._blob_client(container, blob_name)
            stream = blob.download_blob(timeout=self._timeout)
            data = stream.readall()
            return data.decode(encoding)
        except AzureError as exc:
            raise _map_azure_error(exc) from exc

    # PUBLIC_INTERFACE
    def download_bytes(self, container: str, blob_name: str) -> bytes:
        """Download a blob as bytes."""
        try:
            blob = self._blob_client(container, blob_name)
            stream = blob.download_blob(timeout=self._timeout)
            return stream.readall()
        except AzureError as exc:
            raise _map_azure_error(exc) from exc

    # PUBLIC_INTERFACE
    def upload_text(
        self,
        container: str,
        blob_name: str,
        data: str,
        overwrite: Optional[bool] = None,
        content_type: str = "text/plain; charset=utf-8",
        encoding: str = "utf-8",
    ) -> None:
        """Upload text to a blob."""
        eff_overwrite = settings.ALLOW_OVERWRITE if overwrite is None else overwrite
        try:
            blob = self._blob_client(container, blob_name)
            content_settings = ContentSettings(content_type=content_type, content_encoding=encoding)
            blob.upload_blob(
                data.encode(encoding),
                overwrite=eff_overwrite,
                content_settings=content_settings,
                timeout=self._timeout,
            )
        except AzureError as exc:
            raise _map_azure_error(exc) from exc

    # PUBLIC_INTERFACE
    def upload_bytes(
        self,
        container: str,
        blob_name: str,
        data: bytes | io.BytesIO,
        overwrite: Optional[bool] = None,
        content_type: Optional[str] = None,
    ) -> None:
        """Upload bytes to a blob."""
        eff_overwrite = settings.ALLOW_OVERWRITE if overwrite is None else overwrite
        try:
            blob = self._blob_client(container, blob_name)
            kwargs = {"timeout": self._timeout, "overwrite": eff_overwrite}
            if content_type:
                kwargs["content_settings"] = ContentSettings(content_type=content_type)
            blob.upload_blob(data, **kwargs)
        except AzureError as exc:
            raise _map_azure_error(exc) from exc

    # PUBLIC_INTERFACE
    def exists(self, container: str, blob_name: str) -> bool:
        """Check if a blob exists."""
        try:
            blob = self._blob_client(container, blob_name)
            return blob.exists(timeout=self._timeout)
        except AzureError as exc:
            mapped = _map_azure_error(exc)
            # If container or blob not found, exists -> False
            if isinstance(mapped, (BlobNotFoundError, ContainerNotFoundError)):
                return False
            raise mapped from exc
