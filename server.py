"""Horizon Deploy entry point for init-app-mcp.

The application code follows a ``src/`` layout. This small wrapper lets hosts
that require a Python-file entry point import the FastMCP server reliably.
"""

from pathlib import Path
import sys


# Resolve from this file, never from the process working directory.  This is
# an absolute path in every environment, including Horizon's build container.
ABSOLUTE_SOURCE_DIRECTORY = (Path(__file__).resolve().parent / "src").resolve()
if str(ABSOLUTE_SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(ABSOLUTE_SOURCE_DIRECTORY))

from init_app_mcp.server import main, mcp


if __name__ == "__main__":
    # Hosting platforms execute this file directly. Streamable HTTP is the
    # correct transport for a deployed MCP endpoint; the package CLI remains
    # stdio-first for local VS Code clients.
    main(["--transport", "streamable-http", *sys.argv[1:]])
