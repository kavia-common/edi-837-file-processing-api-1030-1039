from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict  # type: ignore


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and optional .env file."""

    APP_NAME: str = Field(default="EDI 837 Processing API", description="Application display name")
    ENV: str = Field(default="development", description="Deployment environment name")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    AZURE_STORAGE_CONNECTION_STRING: str = Field(
        default="",
        description="Azure Storage connection string (do not hardcode in code, set in environment)",
    )

    INPUT_CONTAINER_DEFAULT: str = Field(default="incoming", description="Default input container name")
    OUTPUT_CONTAINER_DEFAULT: str = Field(default="processed", description="Default output container name")
    OUTPUT_PREFIX_DEFAULT: str = Field(default="out/", description="Default output blob prefix")

    BLOB_REQUEST_TIMEOUT_SECS: int = Field(default=60, description="Azure blob request timeout in seconds")
    BLOB_MAX_RETRIES: int = Field(default=3, description="Azure blob request max retries")
    ALLOW_OVERWRITE: bool = Field(default=False, description="Allow overwriting output blobs by default")
    REQUEST_MAX_BODY_MB: int = Field(default=20, description="Max request body in MB")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance to avoid re-reading environment."""
    return Settings()


# Singleton settings
settings = get_settings()
