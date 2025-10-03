from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class LoggerConfig(BaseSettings):
    LEVEL: str | int = Field(default="INFO")
    RENDER_JSON_LOGS: bool = Field(default=False)
    FILE_PATH: Path | None = Field(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOGGER_",
        env_file_encoding="utf-8",
        extra="ignore",
    )
