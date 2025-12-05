from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, UploadFile, Path, Query, status

from src.core.background import JobManager
from src.models.schemas import (
    FileProcessRequest,
    BatchProcessRequest,
    JobResponse,
    JobStatusResponse,
)

router = APIRouter(prefix="/processing", tags=["processing"])


def get_job_manager() -> JobManager:
    """Dependency to fetch the JobManager (singleton in-memory)."""
    return JobManager.instance()


# PUBLIC_INTERFACE
@router.post(
    "/process/file",
    summary="Process a single EDI 837 file",
    description="Accepts a file upload or a blob storage reference to process an EDI 837 payload.",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
)
async def process_file(
    background_tasks: BackgroundTasks,
    payload: Optional[FileProcessRequest] = Body(None, description="Blob reference payload"),
    file: Optional[UploadFile] = File(None, description="Raw EDI 837 file upload"),
    allow_overwrite: Optional[bool] = Query(None, description="Override overwrite behavior for this request"),
    jobs: JobManager = Depends(get_job_manager),
) -> JobResponse:
    """Queue a background job to process a single EDI 837 file.

    Parameters:
      - payload: Optional blob storage reference for the input EDI file.
      - file: Optional direct file upload for processing.
      - allow_overwrite: Whether to allow overwriting existing outputs.
    Returns:
      - JobResponse: Contains job_id and initial status.
    """
    job = jobs.create_job(metadata={"type": "single", "allow_overwrite": allow_overwrite})
    # Placeholder background work; to be implemented in subsequent steps
    background_tasks.add_task(jobs.run_noop_job, job.job_id)
    return JobResponse(job_id=job.job_id, status=job.status)


# PUBLIC_INTERFACE
@router.post(
    "/process/batch",
    summary="Process a batch of EDI 837 files",
    description="Queues a background job to process a batch of inputs from blob storage.",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobResponse,
)
async def process_batch(
    payload: BatchProcessRequest = Body(...),
    jobs: JobManager = Depends(get_job_manager),
) -> JobResponse:
    """Queue a background job to process a batch of EDI 837 files.

    Parameters:
      - payload: BatchProcessRequest describing input and output containers/prefix.
    Returns:
      - JobResponse: Contains job_id and initial status.
    """
    job = jobs.create_job(metadata={"type": "batch", "input": payload.model_dump()})
    jobs.enqueue(job.job_id)  # mark as pending; actual logic in next steps
    return JobResponse(job_id=job.job_id, status=job.status)


# PUBLIC_INTERFACE
@router.get(
    "/jobs/{job_id}",
    summary="Get job status",
    description="Returns the status and details of a background job.",
    response_model=JobStatusResponse,
)
async def get_job_status(
    job_id: str = Path(..., description="The job identifier"),
    jobs: JobManager = Depends(get_job_manager),
) -> JobStatusResponse:
    """Retrieve current job status by id.

    Parameters:
      - job_id: The job identifier UUID string.
    Returns:
      - JobStatusResponse with status and optional error message.
    """
    job = jobs.get(job_id)
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        error=job.error,
        metadata=job.metadata,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
