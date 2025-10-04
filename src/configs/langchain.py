from pydantic import SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class LangchainConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENROUTER_", extra="ignore", env_file=".env"
    )

    API_KEY: SecretStr
    BASE_URL: str
    MODEL: str = "openai/gpt-4o-mini"
    TEMPLATE: str = (
        "Question: {question}\n"
        "Answer: Let's think step by step."
    )