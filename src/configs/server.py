from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SERVER_", extra="ignore", env_file=".env"
    )

    API_PREFIX: str = Field(default="/api")

    API_VERSION: str = Field(default="v1")
    APP_NAME: str = Field(default="finam-mcp")
    NAMESPACE: str = Field(default="dev")
    AUTHOR: str = Field(default="ctrl+alt+profit")

    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
