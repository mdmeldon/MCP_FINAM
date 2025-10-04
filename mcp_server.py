from src import create_mcp_app
from src.configs import Config

cfg = Config()
mcp = create_mcp_app(cfg.SERVER)