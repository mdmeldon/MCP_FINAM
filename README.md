# Hello World MCP Template

Simple Hello World MCP (Model Context Protocol) server template with environment variable examples. This is a minimal template to get started with creating your own MCP servers.

## Features

- Basic "Hello World" functionality
- Environment variable usage examples
- Echo functionality for testing
- Server information endpoint
- Simple error handling
- Logging configuration

## Installation

### Option 1: Using uv (recommended)

```bash
# Clone or copy this template
cd mcp_template

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
uv pip install -e .
```

### Connecting to Claude Desktop or Cursor

Add this configuration to your `claude_desktop_config.json` or MCP configuration:

```json
{
  "mcpServers": {
    "mcp_template": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/olegstefanov/Base/Prog/mcp_template", // путь до папки с MCP
        "server"
      ],
      "env": {
        "TEST_ENV": "dawjdkawnkdakwd"
      },
      "description": "MCP server for getting templates"
    }
  }
}
```

## Available Tools

### `hello`
Returns a hello message with optional personalization.

**Parameters:**
- `name` (optional): Name to greet

**Example:**
```python
# Basic hello
{"tool": "hello"}
# Returns: {"success": true, "message": "Hello, World!", "timestamp": "2024-01-01T00:00:00Z"}

# Personalized hello
{"tool": "hello", "name": "Alice"}
# Returns: {"success": true, "message": "Hello, Alice!", "timestamp": "2024-01-01T00:00:00Z"}
```

### `get_env_info`
Returns information from environment variables.

**Parameters:** None

**Example:**
```python
{"tool": "get_env_info"}
# Returns: {
#   "success": true,
#   "test_env": "value"
# }
```

## Development

### Project Structure

```
mcp_template/
├── server.py              # Main MCP server implementation
├── pyproject.toml         # Project configuration and dependencies
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### Adding New Tools

To add a new tool to your MCP server:

1. Define a new function with the `@mcp.tool()` decorator:

```python
@mcp.tool("your_tool_name")
def your_tool_function(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """
    Description of your tool.
    
    Parameters:
    - param1: Description of parameter 1
    - param2: Description of parameter 2 (optional)
    
    Returns:
    - Description of return value
    """
    try:
        # Your tool logic here
        result = f"Processing {param1} with {param2}"
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error in your_tool_function: {e}")
        return {
            "success": False,
            "error": str(e)
        }
```

2. Update the `get_server_info` function to include your new tool in the `available_tools` list.

### Environment Variables

The template demonstrates how to use environment variables in MCP servers:

- Use `python-dotenv` to load variables from `.env` file
- Use `os.getenv()` with default values for robust configuration
- Keep sensitive information in environment variables, not in code

### Error Handling

The template includes basic error handling patterns:

- Try-catch blocks around tool logic
- Consistent error response format
- Logging for debugging
- Graceful degradation with default values

## License

MIT License - feel free to use this template for your own MCP servers.

## Contributing

This is a template project. Feel free to modify and extend it for your needs.

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you've installed the dependencies and activated your virtual environment.

2. **Environment variables not loading**: Check that your `.env` file is in the same directory as `server.py` and has the correct format.

3. **MCP connection issues**: Verify the path in your MCP configuration is correct and the server starts without errors.

### Debugging

Enable debug mode by setting `DEBUG=true` in your `.env` file for more verbose logging.

### Getting Help

- Check the [MCP documentation](https://modelcontextprotocol.io/)
- Review the server logs for error messages
- Ensure all dependencies are correctly installed 