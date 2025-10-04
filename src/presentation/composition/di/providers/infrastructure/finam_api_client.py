from dishka import Provider, provide, Scope
from pydantic_settings import BaseSettings

from src.infrastructure.core.finam_client import FinamClient


class FinamApiClientProvider(Provider):
    def __init__(self, cfg: BaseSettings):
        super().__init__(scope=Scope.REQUEST)
        self.cfg = cfg

    @provide(scope=Scope.REQUEST)
    def provide_client(self) -> FinamClient:
        return FinamClient(token=self.cfg.TOKEN)