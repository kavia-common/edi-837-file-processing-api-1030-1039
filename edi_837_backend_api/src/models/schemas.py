from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


# Requests

class BlobRef(BaseModel):
    container: str = Field(..., description="Azure Blob container name")
    blob_name: str = Field(..., description="Blob name/path in the container")
    prefix: Optional[str] = Field(None, description="Optional output prefix for results")


class FileProcessRequest(BaseModel):
    input: Optional[BlobRef] = Field(None, description="Blob reference to the input EDI file")
    output: Optional[BlobRef] = Field(None, description="Blob reference for output location")
    allow_overwrite: Optional[bool] = Field(None, description="Override default overwrite behavior")


class BatchProcessRequest(BaseModel):
    input_container: str = Field(..., description="Input container name")
    input_prefix: str = Field(..., description="Prefix path for batch inputs")
    output_container: str = Field(..., description="Output container name")
    output_prefix: str = Field(..., description="Prefix for produced JSON outputs")
    allow_overwrite: Optional[bool] = Field(None, description="Override default overwrite behavior for the batch")


# Responses

class JobResponse(BaseModel):
    job_id: str = Field(..., description="Identifier for the queued job")
    status: str = Field(..., description="Initial status of the job")


class JobStatusResponse(BaseModel):
    job_id: str = Field(..., description="Identifier for the job")
    status: str = Field(..., description="Current status of the job")
    error: Optional[str] = Field(None, description="Error message if job failed")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional job metadata")
    started_at: Optional[str] = Field(None, description="UTC timestamp when job started (ISO8601)")
    completed_at: Optional[str] = Field(None, description="UTC timestamp when job completed (ISO8601)")


# Normalized Claim Schema (shells/placeholders)

class NormalizedClaim(BaseModel):
    """Placeholder for a normalized 837 claim schema."""
    claim_id: Optional[str] = None
    patient: Optional[Dict[str, Any]] = None
    provider: Optional[Dict[str, Any]] = None
    services: Optional[list[Dict[str, Any]]] = None
