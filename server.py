from src.configs import Config
from src.presentation.langchain.main import create_langchain_app


if __name__ == "__main__":
    cfg = Config()

    create_langchain_app(cfg.LANGCHAIN)