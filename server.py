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
    main()
