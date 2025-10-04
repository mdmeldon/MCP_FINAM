from pydantic import Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class LangchainConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENROUTER_", extra="ignore", env_file=".env"
    )

    API_KEY: SecretStr
    FINAM_API_TOKEN: SecretStr = Field(validation_alias="FINAM_API_TOKEN")
    FINAM_ACCOUNT_ID: SecretStr = Field(validation_alias="FINAM_ACCOUNT_ID")
    BASE_URL: str
    MODEL: str = "openai/gpt-4o-mini"
    TEMPLATE: str = (
        "Question: {question}\n"
        "Answer: Let's think step by step."
    )
