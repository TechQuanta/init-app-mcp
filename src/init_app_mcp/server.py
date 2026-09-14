"""The FastMCP stdio server for init-app."""

from __future__ import annotations

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


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
