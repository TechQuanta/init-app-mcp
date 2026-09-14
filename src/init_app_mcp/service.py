"""Validated, side-effect-aware operations shared by MCP tools and tests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import __version__, catalog


PROJECT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
STRATEGIES = catalog.STRATEGIES

BLUEPRINT_SIGNALS = (
    ("mcp", ("mcp", "model context protocol", "agent tool", "tool server")),
    ("rag_ai", ("rag", "retrieval augmented", "vector database", "vector store")),
    ("mlops_core", ("mlops", "model training", "model serving", "machine learning pipeline")),
    ("dbt_analytics", ("dbt", "data warehouse", "analytics transformation")),
    ("data_pipeline", ("etl", "data pipeline", "workflow orchestration", "prefect", "dagster")),
    ("hp_cli", ("command line", " cli", "terminal application", "typer", "click")),
    ("fastapi", ("fastapi",)),
    ("django", ("django", "admin panel", "admin site")),
    ("flask", ("flask",)),
    ("bottle", ("bottle",)),
    ("sanic", ("sanic",)),
    ("falcon", ("falcon",)),
    ("tornado", ("tornado",)),
    ("pyramid", ("pyramid",)),
)


def _validate_project_name(project_name: str) -> str:
    if not PROJECT_NAME.fullmatch(project_name):
        raise ValueError(
            "project_name must start with a letter and contain only letters, "
            "numbers, underscores, or hyphens (maximum 64 characters)."
        )
    return project_name


def _frameworks() -> tuple[str, ...]:
    return tuple(catalog.BLUEPRINTS)


def _validate_request(
    project_name: str,
    framework: str,
    strategy: str,
    database: str,
    server: str | None,
) -> tuple[str, str, str, str, str | None]:
    name = _validate_project_name(project_name)
    framework = framework.lower().strip()
    strategy = strategy.lower().strip()
    database = database.lower().strip()
    server = server.lower().strip() if server else None

    if framework not in _frameworks():
        raise ValueError(f"Unsupported framework: {framework}.")
    if strategy not in STRATEGIES:
        raise ValueError(f"Unsupported strategy: {strategy}.")
    if database not in catalog.DATABASES:
        raise ValueError(f"Unsupported database: {database}.")
    allowed_servers = catalog.BLUEPRINTS[framework]["servers"]
    if server and server not in allowed_servers:
        raise ValueError(
            f"Unsupported server '{server}' for {framework}. "
            f"Choose one of: {', '.join(allowed_servers)}."
        )
    return name, framework, strategy, database, server


def library_metadata() -> dict[str, Any]:
    """Return stable metadata that clients can inspect before calling tools."""
    return {
        "name": "init-app-mcp",
        "version": __version__,
        "target_cli": "init-app",
        "catalog_version": catalog.INIT_APP_VERSION,
        "description": "Independent FastMCP server that recommends init-app commands.",
        "generation_flow": [
            "get_init_app_command_metadata",
            "recommend_init_app_flags",
            "build_init_app_command",
        ],
        "safety": "This server only returns metadata and command recommendations; it does not create files.",
    }


def list_blueprints() -> list[dict[str, Any]]:
    """Build client-friendly capability metadata directly from init-app constants."""
    return catalog.list_blueprints()


def command_metadata() -> dict[str, Any]:
    """Return the independent, machine-readable init-app CLI contract."""
    return catalog.command_metadata()


def project_command_preview(
    project_name: str,
    framework: str = "fastapi",
    strategy: str = "standard",
    database: str = "sqlite",
    server: str | None = None,
    venv: bool = True,
    drf: bool = False,
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Validate a generation request and return a portable CLI argument list."""
    name, framework, strategy, database, server = _validate_request(
        project_name, framework, strategy, database, server
    )
    args = ["init-app", name, "--framework", framework, "--type", strategy]
    args.extend(["--db", database, "--venv", "y" if venv else "n"])
    if server:
        args.extend(["--server", server])
    if drf:
        if framework != "django":
            raise ValueError("drf is only available for the django framework.")
        args.append("--drf")
    target = None
    if output_dir:
        target = str(Path(output_dir).expanduser().resolve() / name)
        args.extend(["--output-dir", str(Path(output_dir).expanduser().resolve())])
    return {"valid": True, "arguments": args, "target_directory": target}


def recommend_flags(requirements: str) -> dict[str, Any]:
    """Recommend supported flags from plain-English user requirements.

    This is intentionally deterministic: it gives an LLM a library-grounded
    starting point and explains the signals used, while the LLM can still ask
    the user follow-up questions before presenting the command.
    """
    if not requirements or not requirements.strip():
        raise ValueError("requirements must describe the project to generate.")
    text = requirements.casefold()

    framework = "fastapi"
    matches: list[str] = []
    for candidate, signals in BLUEPRINT_SIGNALS:
        found = [signal for signal in signals if signal in text]
        if found:
            framework = candidate
            matches = found
            break

    database = "sqlite"
    database_reason = "SQLite is the portable default when no database is requested."
    for candidate, signals in (
        ("postgresql", ("postgres", "postgresql")),
        ("mongodb", ("mongodb", "mongo", "document database")),
        ("mysql", ("mysql",)),
    ):
        if any(signal in text for signal in signals):
            database = candidate
            database_reason = f"Requirement mentions {candidate}."
            break

    production_signals = (
        "production", "deploy", "docker", "kubernetes", "k8s", "ci/cd", "jenkins",
    )
    if any(signal in text for signal in production_signals):
        strategy = "production"
    elif "auto_config" in text or "auto config" in text:
        strategy = "auto_config"
    elif "custom folder" in text or "custom structure" in text:
        strategy = "custom"
    else:
        strategy = "standard"

    drf = framework == "django" and any(
        signal in text for signal in ("rest api", "restful", "api endpoint", "django rest")
    )
    server = None
    if strategy == "production":
        server = {"fastapi": "gunicorn", "flask": "gunicorn", "django": "gunicorn"}.get(framework)

    framework_reason = (
        f"Matched requirement terms: {', '.join(matches)}."
        if matches
        else "No framework-specific term matched; FastAPI is the API-oriented default."
    )
    return {
        "selection": {
            "framework": framework,
            "strategy": strategy,
            "database": database,
            "server": server,
            "drf": drf,
            "venv": True,
        },
        "recommended_flags": [
            {"flag": "--framework", "value": framework},
            {"flag": "--type", "value": strategy},
            {"flag": "--db", "value": database},
            {"flag": "--venv", "value": "y"},
        ]
        + ([{"flag": "--server", "value": server}] if server else [])
        + ([{"flag": "--drf", "value": True}] if drf else []),
        "reasoning": [framework_reason, database_reason],
        "questions": [
            "What project name should be used?",
            "Which output directory should contain the project?",
        ]
        + (["SQLite was selected as the default. Do you need another database?"] if database == "sqlite" else []),
        "next_step": "Confirm or edit the selection, then call build_init_app_command.",
    }
