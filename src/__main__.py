from src.configs import Config
from src.presentation.mcp import create_mcp_app

if __name__ == "__main__":
    cfg = Config()
    mcp = create_mcp_app(cfg.SERVER)

    mcp.run(transport="streamable-http")