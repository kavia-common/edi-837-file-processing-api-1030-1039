from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and optional .env file.

    Notes:
      - Uses python-dotenv via pydantic-settings to load a local .env file.
      - Extra/unknown environment variables are ignored to avoid build-time failures when new vars are introduced.
      - Do not log secrets in this module.
    """

    # Core app config
    APP_NAME: str = Field(default="EDI 837 Processing API", description="Application display name")
    ENV: str = Field(default="development", description="Deployment environment name")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Azure
    AZURE_STORAGE_CONNECTION_STRING: str = Field(
        default="",
        description="Azure Storage connection string (do not hardcode in code, set in environment)",
    )

    # Processing defaults
    INPUT_CONTAINER_DEFAULT: str = Field(default="incoming", description="Default input container name")
    OUTPUT_CONTAINER_DEFAULT: str = Field(default="processed", description="Default output container name")
    OUTPUT_PREFIX_DEFAULT: str = Field(default="out/", description="Default output blob prefix")

    # Azure client behavior
    BLOB_REQUEST_TIMEOUT_SECS: int = Field(default=60, description="Azure blob request timeout in seconds")
    BLOB_MAX_RETRIES: int = Field(default=3, description="Azure blob request max retries")
    ALLOW_OVERWRITE: bool = Field(default=False, description="Allow overwriting output blobs by default")
    REQUEST_MAX_BODY_MB: int = Field(default=20, description="Max request body in MB")

    # Optional environment compatibility fields (accept but not strictly required)
    backend_url: Optional[str] = Field(default=None, description="Backend base URL")
    frontend_url: Optional[str] = Field(default=None, description="Frontend base URL")
    ws_url: Optional[str] = Field(default=None, description="WebSocket base URL")
    site_url: Optional[str] = Field(default=None, description="Public site URL for callbacks/redirects")
    allowed_origins: List[str] = Field(default_factory=list, description="CORS allowed origins")
    allowed_headers: List[str] = Field(default_factory=list, description="CORS allowed headers")
    allowed_methods: List[str] = Field(default_factory=list, description="CORS allowed methods")
    cors_max_age: Optional[int] = Field(default=None, description="CORS preflight max age (seconds)")
    cookie_domain: Optional[str] = Field(default=None, description="Cookie domain")
    trust_proxy: Optional[bool] = Field(default=None, description="Whether to trust X-Forwarded-* headers")
    host: Optional[str] = Field(default=None, description="Service host binding")
    uvicorn_host: Optional[str] = Field(default=None, description="Uvicorn host override")
    uvicorn_workers: Optional[int] = Field(default=None, description="Uvicorn workers count")
    node_env: Optional[str] = Field(default=None, description="Node.js-like environment flag for compatibility")
    request_timeout_ms: Optional[int] = Field(default=None, description="Request timeout in milliseconds")
    rate_limit_window_s: Optional[int] = Field(default=None, description="Rate limit window in seconds")
    rate_limit_max: Optional[int] = Field(default=None, description="Max requests per rate limit window")
    port: Optional[int] = Field(default=None, description="Service port")

    # pydantic-settings configuration:
    # - env_file enables dotenv loading
    # - extra="ignore" prevents ValidationError when unknown env keys are present
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance to avoid re-reading environment."""
    return Settings()


# Singleton settings; safe at import time because Settings ignores unknown env vars
settings = get_settings()
