"""The FastMCP server for init-app, with stdio and HTTP transports."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - depends on package installation.
    raise SystemExit(
        "init-app-mcp requires FastMCP. "
        "Install dependencies with: python -m pip install 'fastmcp>=2,<3'"
    ) from exc

# Keep package imports absolute.  When this module is invoked directly as
# ``python server.py`` from ``src/init_app_mcp``, add its absolute ``src``
# directory so the package remains importable without depending on CWD.
ABSOLUTE_SOURCE_DIRECTORY = Path(__file__).resolve().parent.parent
if str(ABSOLUTE_SOURCE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(ABSOLUTE_SOURCE_DIRECTORY))

from init_app_mcp import service


# This module-level object is the MCP server. FastMCP reads the type hints,
# parameter defaults, and docstrings below to publish its tool schemas to LLMs.
mcp = FastMCP("init-app")
TOOL_NAMES = (
    "build_init_app_command",
    "get_init_app_command_metadata",
    "list_tool_domains",
    "select_domain_tools",
    "list_project_blueprints",
    "recommend_init_app_flags",
)


@mcp.tool()
def get_init_app_command_metadata() -> dict[str, Any]:
    """First step: return init-app command metadata, flags, values, and workflow."""
    return {**service.library_metadata(), **service.command_metadata()}


@mcp.tool()
def list_tool_domains() -> list[dict[str, Any]]:
    """List parent domains such as research, writing, resume, and code with child tools."""
    return service.list_tool_domains()


@mcp.tool()
def select_domain_tools(domain: str, tools: list[str] | None = None) -> dict[str, Any]:
    """Select and validate multiple child tools under one parent domain."""
    return service.select_domain_tools(domain, tools)


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
    env_manager: str | None = None,
    drf: bool = False, output_dir: str | None = None, spec_path: str | None = None,
    dry_run: bool = False, force: bool = False, app_name: str | None = None,
    folders: list[str] | None = None, packages: list[str] | None = None,
) -> dict[str, Any]:
    """Final step: validate confirmed user selections and return an init-app command without running it."""
    return service.project_command_preview(
        project_name, framework, strategy, database, server, venv, drf, output_dir,
        spec_path, dry_run, force, app_name, folders, packages, env_manager=env_manager,
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
        choices=("stdio", "sse", "http", "streamable-http"),
        default="stdio",
        help="MCP transport to run (default: stdio). Use http or streamable-http for hosted deployments.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "127.0.0.1"),
        help="Host for HTTP transports (default: HOST environment variable or 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port for HTTP transports (default: PORT environment variable or 8000).",
    )
    args = parser.parse_args(argv)

    if args.list_tools:
        print(
            json.dumps(
                {"server": mcp.name, "tools": sorted(TOOL_NAMES)},
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
    transport = "http" if args.transport == "streamable-http" else args.transport
    run_options: dict[str, Any] = {"transport": transport}
    if transport != "stdio":
        run_options.update({"host": args.host, "port": args.port})
        if transport == "http":
            run_options["path"] = "/mcp"
    mcp.run(**run_options)


if __name__ == "__main__":
    main()
