from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging import logger, bind_request_context, unbind_request_context
from src.core.errors import register_exception_handlers
from src.api.routers.processing import router as processing_router


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log structured request/response lifecycle with request_id/job_id correlation."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Bind per-request context (request_id)
        bind_request_context(request)
        logger.info("request.start", extra={"method": request.method, "path": request.url.path})
        try:
            response = await call_next(request)
        except Exception as exc:  # Let exception handlers log as needed
            logger.exception("request.unhandled_exception")
            unbind_request_context()
            raise exc
        logger.info(
            "request.end",
            extra={
                "status_code": response.status_code,
                "method": request.method,
                "path": request.url.path,
            },
        )
        unbind_request_context()
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan to initialize resources in future steps (e.g., blob clients, pools)."""
    logger.info("app.startup", extra={"env": settings.ENV})
    yield
    logger.info("app.shutdown")


# Initialize FastAPI app with metadata and tags
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API for processing EDI 837 files from Azure Blob storage, enriching and exporting JSON.",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Service health endpoints"},
        {"name": "processing", "description": "Endpoints to process EDI 837 files and manage jobs"},
    ],
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # To be restricted via environment later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware
app.add_middleware(LoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check", description="Returns service health status.")
def health_check() -> dict:
    """Health check endpoint used for liveness/readiness checks.

    Returns:
        A JSON object indicating service health.
    """
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.ENV}


# Include processing router
app.include_router(processing_router, prefix="/api")
