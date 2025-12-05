import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class JobInfo:
    job_id: str
    status: JobStatus = JobStatus.PENDING
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class JobManager:
    """In-memory job manager; to be replaced with persistent queue in the future."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._jobs: Dict[str, JobInfo] = {}
        self._jobs_lock = threading.Lock()

    @classmethod
    def instance(cls) -> "JobManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = JobManager()
        return cls._instance

    # PUBLIC_INTERFACE
    def create_job(self, metadata: Optional[Dict[str, Any]] = None) -> JobInfo:
        """Create and register a new job with pending status."""
        job_id = str(uuid.uuid4())
        job = JobInfo(job_id=job_id, status=JobStatus.PENDING, metadata=metadata or {})
        with self._jobs_lock:
            self._jobs[job_id] = job
        return job

    # PUBLIC_INTERFACE
    def enqueue(self, job_id: str) -> None:
        """Set job to pending (no-op for now)."""
        with self._jobs_lock:
            job = self._jobs[job_id]
            job.status = JobStatus.PENDING

    # PUBLIC_INTERFACE
    def start(self, job_id: str) -> None:
        """Mark a job as running."""
        with self._jobs_lock:
            job = self._jobs[job_id]
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow().isoformat()

    # PUBLIC_INTERFACE
    def complete(self, job_id: str) -> None:
        """Mark a job as completed."""
        with self._jobs_lock:
            job = self._jobs[job_id]
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow().isoformat()

    # PUBLIC_INTERFACE
    def fail(self, job_id: str, error: str) -> None:
        """Mark a job as failed with an error message."""
        with self._jobs_lock:
            job = self._jobs[job_id]
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.utcnow().isoformat()

    # PUBLIC_INTERFACE
    def get(self, job_id: str) -> JobInfo:
        """Get job info."""
        with self._jobs_lock:
            return self._jobs[job_id]

    # PUBLIC_INTERFACE
    def run_noop_job(self, job_id: str, delay_seconds: float = 0.1) -> None:
        """Run a placeholder job that waits for a moment and completes."""
        try:
            self.start(job_id)
            time.sleep(delay_seconds)
            self.complete(job_id)
        except Exception as exc:  # pragma: no cover
            self.fail(job_id, str(exc))
