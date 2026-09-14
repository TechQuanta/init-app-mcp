"""The FastMCP stdio server for init-app."""

from __future__ import annotations

import argparse
import json
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - depends on package installation.
    raise SystemExit(
        "init-app-mcp requires the FastMCP v1 SDK. "
        "Install dependencies with: python -m pip install 'mcp>=1,<2'"
    ) from exc

from . import service


# This module-level object is the MCP server. FastMCP reads the type hints,
# parameter defaults, and docstrings below to publish its tool schemas to LLMs.
mcp = FastMCP("init-app")


@mcp.tool()
def get_init_app_command_metadata() -> dict[str, Any]:
    """First step: return init-app command metadata, flags, values, and workflow."""
    return {**service.library_metadata(), **service.command_metadata()}


@mcp.tool()
def list_project_blueprints() -> list[dict[str, Any]]:
    """List every web and specialized project type supported by init-app."""
    return service.list_blueprints()


@mcp.tool()
def recommend_init_app_flags(requirements: str) -> dict[str, Any]:
    """Second step: derive supported init-app flags and clarification questions from a user query."""
    return service.recommend_flags(requirements)


@mcp.tool()
def build_init_app_command(
    project_name: str, framework: str = "fastapi", strategy: str = "standard",
    database: str = "sqlite", server: str | None = None, venv: bool = True,
    drf: bool = False, output_dir: str | None = None,
) -> dict[str, Any]:
    """Final step: validate confirmed user selections and return an init-app command without running it."""
    return service.project_command_preview(
        project_name, framework, strategy, database, server, venv, drf, output_dir
    )


def build_server() -> FastMCP:
    """Return the configured server for embedding or test clients."""
    return mcp


def main(argv: list[str] | None = None) -> None:
    """Start MCP stdio transport or print safe local diagnostics."""
    parser = argparse.ArgumentParser(description="Run the init-app FastMCP server.")
    parser.add_argument(
        "--list-tools",
        action="store_true",
        help="Print the tool names and exit without starting the MCP transport.",
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help="Print init-app command metadata and exit without starting the MCP transport.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport to run (default: stdio). Use streamable-http for local HTTP testing.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transports (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transports (default: 8000).",
    )
    args = parser.parse_args(argv)

    if args.list_tools:
        print(
            json.dumps(
                {"server": mcp.name, "tools": sorted(mcp._tool_manager._tools)},
                indent=2,
            )
        )
        return
    if args.metadata:
        print(
            json.dumps(
                {**service.library_metadata(), **service.command_metadata()},
                indent=2,
            )
        )
        return

    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535.")
    mcp.settings.host = args.host
    mcp.settings.port = args.port
    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
