from typing import Optional


class AzureBlobService:
    """Azure Blob service wrapper. Implementation will be added in the next step."""

    def __init__(self, connection_string: Optional[str] = None) -> None:
        self._conn_str = connection_string

    # PUBLIC_INTERFACE
    def download_text(self, container: str, blob_name: str, encoding: str = "utf-8") -> str:
        """Download a blob as text. To be implemented."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def upload_text(self, container: str, blob_name: str, data: str, overwrite: bool = False) -> None:
        """Upload text to a blob. To be implemented."""
        raise NotImplementedError

    # PUBLIC_INTERFACE
    def exists(self, container: str, blob_name: str) -> bool:
        """Check if a blob exists. To be implemented."""
        raise NotImplementedError
