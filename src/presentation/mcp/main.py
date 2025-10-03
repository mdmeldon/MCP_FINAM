from mcp.server.fastmcp import FastMCP

from src.configs import Config
from src.presentation.mcp.handlers import init_tools


def create_mcp_app():
    cfg = Config()

    mcp = FastMCP(
        name=cfg.SERVER.APP_NAME,
        host=cfg.SERVER.HOST,
        port=cfg.SERVER.PORT,
    )

    init_tools(mcp)

    # mcp.run(transport="streamable-http")

    return mcp