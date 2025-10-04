from mcp.server.fastmcp import FastMCP

from src.configs import ServerConfig
from src.presentation.mcp.handlers import init_tools


def create_mcp_app(cfg: ServerConfig):
    mcp = FastMCP(
        name=cfg.APP_NAME,
        host=cfg.HOST,
        port=cfg.PORT,
    )

    init_tools(mcp)

    return mcp