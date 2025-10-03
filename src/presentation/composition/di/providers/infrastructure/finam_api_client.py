from dishka import Provider, provide, Scope
from pydantic_settings import BaseSettings

from src.infrastructure.core.client import Client


class FinamApiClientProvider(Provider):
    def __init__(self, cfg: BaseSettings):
        super().__init__(scope=Scope.REQUEST)
        self.cfg = cfg

    @provide(scope=Scope.REQUEST)
    def provide_client(self) -> Client:
        return Client(token=self.cfg.TOKEN)