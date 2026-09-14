"""Horizon Deploy entry point for init-app-mcp.

The application code follows a ``src/`` layout. This small wrapper lets hosts
that require a Python-file entry point import the FastMCP server reliably.
"""

from pathlib import Path
import sys


SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from init_app_mcp.server import main, mcp


if __name__ == "__main__":
    # Hosting platforms execute this file directly. Streamable HTTP is the
    # correct transport for a deployed MCP endpoint; the package CLI remains
    # stdio-first for local VS Code clients.
    main(["--transport", "streamable-http", *sys.argv[1:]])
