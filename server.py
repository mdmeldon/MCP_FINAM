from mcp.server.fastmcp import FastMCP
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# MCP initialization
mcp = FastMCP(
    name="Hello World MCP",
    description="Simple Hello World MCP server with environment variable example",
    version="1.0.0",
    author="MCP Developer",
)

@mcp.tool("hello")
def hello(name: Optional[str] = None) -> Dict[str, Any]:
    """
    Returns a hello message.
    
    Parameters:
    - name: Optional name to greet (string)
    
    Returns:
    - Hello message with optional personalization
    """
    try:
        if name:
            message = f"Hello, {name}!"
        else:
            message = "Hello, World!"
        
        return {
            "success": True,
            "message": message,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error in hello function: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool("get_env_info")
def get_env_info() -> Dict[str, Any]:
    """
    Returns information from environment variables.
    
    Returns:
    - Environment variable information
    """
    try:
        # Get environment variable with default value
        test_env = os.getenv("TEST_ENV", "Default MCP App")
        
        return {
            "success": True,
            "test_env": test_env
        }
    except Exception as e:
        logger.error(f"Error getting environment info: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Main function to run the MCP server."""
    logger.info("Starting Hello World MCP server...")
    mcp.run()


if __name__ == "__main__":
    main() 