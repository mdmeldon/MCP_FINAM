from pydantic import Field
from pydantic_settings import BaseSettings

from .logger import LoggerConfig
from .server import ServerConfig
from .langchain import LangchainConfig

class Config(BaseSettings):
    SERVER: ServerConfig = Field(default_factory=ServerConfig)
    LOGGER: LoggerConfig = Field(default_factory=LoggerConfig)
    LANGCHAIN: LangchainConfig = Field(default_factory=LangchainConfig)