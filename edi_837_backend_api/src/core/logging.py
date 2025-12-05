import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

from src.core.config import settings

# Context variables to hold correlation info
_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_job_id_ctx: ContextVar[Optional[str]] = ContextVar("job_id", default=None)


class JsonFormatter(logging.Formatter):
    """Format logs as structured JSON with correlation ids."""

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        # Support passing "extra" dict in logger calls
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)

        req_id = _request_id_ctx.get()
        job_id = _job_id_ctx.get()
        if req_id:
            payload["request_id"] = req_id
        if job_id:
            payload["job_id"] = job_id

        # Add standard attributes if present
        payload["module"] = record.module
        payload["funcName"] = record.funcName
        payload["lineno"] = record.lineno

        return json.dumps(payload, ensure_ascii=False)


def _build_logger() -> logging.Logger:
    log = logging.getLogger("edi837")
    log.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    log.handlers = [handler]
    log.propagate = False
    return log


# Global logger
logger = _build_logger()


# PUBLIC_INTERFACE
def bind_request_context(request) -> None:
    """Bind request_id from headers or generate a new one to the logging context."""
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    _request_id_ctx.set(request_id)


# PUBLIC_INTERFACE
def unbind_request_context() -> None:
    """Clear the request context values."""
    _request_id_ctx.set(None)
    _job_id_ctx.set(None)


# PUBLIC_INTERFACE
def bind_job_id(job_id: Optional[str]) -> None:
    """Bind a job_id to the logging context for correlation."""
    _job_id_ctx.set(job_id)
