"""Validated, side-effect-aware operations shared by MCP tools and tests."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import __version__, catalog


PROJECT_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,62}$")
APP_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
STRATEGIES = catalog.STRATEGIES
ENV_MANAGERS = ("venv", "uv", "none")
DBT_ADAPTERS = catalog.DBT_ADAPTERS

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


def _validate_app_name(app_name: str | None) -> str | None:
    if app_name is None:
        return None
    value = app_name.strip()
    if not APP_NAME.fullmatch(value):
        raise ValueError("app_name must be a valid Python package identifier.")
    return value


def _validate_relative_paths(values: list[str] | None, field: str) -> list[str]:
    if values is None:
        return []
    if not all(isinstance(value, str) for value in values):
        raise ValueError(f"{field} must contain only relative path strings.")
    result: list[str] = []
    for raw in values:
        value = raw.replace("\\", "/").strip().strip("/")
        if not value or ":" in value or any(part in {"", ".", ".."} for part in value.split("/")):
            raise ValueError(f"{field} contains an unsafe path: {raw!r}.")
        if value not in result:
            result.append(value)
    return result


def _validate_dbt_options(
    framework: str, adapter: str, adapter_package: str | None, adapter_type: str | None,
    profile: str | None, target: str,
) -> tuple[str, str | None, str | None, str | None, str]:
    if framework != "dbt_analytics":
        if any(value is not None for value in (adapter_package, adapter_type, profile)) or adapter != "duckdb" or target != "dev":
            raise ValueError("dbt options are only available for the dbt_analytics framework.")
        return adapter, adapter_package, adapter_type, profile, target
    adapter = adapter.lower().strip()
    if adapter not in DBT_ADAPTERS:
        raise ValueError(f"Unsupported dbt adapter: {adapter}.")
    if adapter == "custom":
        if not adapter_package or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", adapter_package):
            raise ValueError("custom dbt adapter requires a safe adapter_package.")
        if not adapter_type or not APP_NAME.fullmatch(adapter_type):
            raise ValueError("custom dbt adapter requires an adapter_type.")
    elif adapter_package or adapter_type:
        raise ValueError("adapter_package and adapter_type are only valid for the custom dbt adapter.")
    for label, value in (("profile", profile), ("target", target)):
        if value is not None and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", value):
            raise ValueError(f"dbt {label} must be a safe identifier.")
    return adapter, adapter_package, adapter_type, profile, target


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
        "tool_domains": catalog.list_tool_domains(),
        "safety": "This server only returns metadata and command recommendations; it does not create files.",
    }


def list_blueprints() -> list[dict[str, Any]]:
    """Build client-friendly capability metadata directly from init-app constants."""
    return catalog.list_blueprints()


def command_metadata() -> dict[str, Any]:
    """Return the independent, machine-readable init-app CLI contract."""
    return catalog.command_metadata()


def list_tool_domains() -> list[dict[str, Any]]:
    """Return the parent domains and child tools exposed by this server."""
    return catalog.list_tool_domains()


def select_domain_tools(domain: str, tools: list[str] | None = None) -> dict[str, Any]:
    """Validate a parent domain and optional child-tool selection."""
    key = domain.strip().lower()
    details = catalog.TOOL_DOMAINS.get(key)
    if details is None:
        raise ValueError(f"Unsupported tool domain: {domain}.")
    available = list(details["tools"])
    selected = available if tools is None else list(dict.fromkeys(tools))
    unknown = [tool for tool in selected if tool not in available]
    if unknown:
        raise ValueError(f"Unsupported tools for {key}: {', '.join(unknown)}.")
    return {"domain": key, "description": details["description"], "available_tools": available, "selected_tools": selected}


def project_command_preview(
    project_name: str,
    framework: str = "fastapi",
    strategy: str = "standard",
    database: str = "sqlite",
    server: str | None = None,
    venv: bool = True,
    drf: bool = False,
    output_dir: str | None = None,
    spec_path: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    app_name: str | None = None,
    apps: list[str] | None = None,
    folders: list[str] | None = None,
    packages: list[str] | None = None,
    env_manager: str | None = None,
    dbt_adapter: str = "duckdb",
    dbt_adapter_package: str | None = None,
    dbt_adapter_type: str | None = None,
    dbt_profile: str | None = None,
    dbt_target: str = "dev",
) -> dict[str, Any]:
    """Validate a generation request and return a portable CLI argument list."""
    name, framework, strategy, database, server = _validate_request(
        project_name, framework, strategy, database, server
    )
    if framework == "dbt_analytics":
        # Warehouse connection is selected by --dbt-adapter, not the app DB flag.
        database = "none"
    env_manager = env_manager or ("venv" if venv else "none")
    if env_manager not in ENV_MANAGERS:
        raise ValueError(f"Unsupported environment manager: {env_manager}.")
    app_name = _validate_app_name(app_name)
    if apps is not None:
        if framework != "django":
            raise ValueError("apps is only available for the django framework.")
        if not apps:
            raise ValueError("apps must contain at least one Django app name.")
        app_names = [_validate_app_name(value) for value in apps]
    else:
        app_names = [app_name] if app_name else []
    folders = _validate_relative_paths(folders, "folders")
    packages = _validate_relative_paths(packages, "packages")
    if packages and strategy != "custom":
        raise ValueError("packages are only available with the custom strategy.")
    if packages and not set(packages).issubset(folders):
        raise ValueError("every package must also appear in folders.")
    if folders and strategy != "custom":
        raise ValueError("folders are only available with the custom strategy.")
    dbt_adapter, dbt_adapter_package, dbt_adapter_type, dbt_profile, dbt_target = _validate_dbt_options(
        framework, dbt_adapter, dbt_adapter_package, dbt_adapter_type, dbt_profile, dbt_target,
    )

    args = ["init-app", name, "--framework", framework, "--type", strategy]
    if spec_path:
        args.extend(["--spec", spec_path])
    if framework != "dbt_analytics":
        args.extend(["--db", database])
    if env_manager == "uv":
        args.extend(["--env-manager", "uv"])
    else:
        args.extend(["--venv", "y" if env_manager == "venv" else "n"])
    if server:
        args.extend(["--server", server])
    if drf:
        if framework != "django":
            raise ValueError("drf is only available for the django framework.")
        args.append("--drf")
    if app_name and framework != "dbt_analytics":
        args.extend(["--app-name", app_name])
    if apps:
        args.extend(["--apps", *app_names])
    if framework == "dbt_analytics":
        args.extend(["--dbt-adapter", dbt_adapter])
        if dbt_adapter_package:
            args.extend(["--dbt-adapter-package", dbt_adapter_package])
        if dbt_adapter_type:
            args.extend(["--dbt-adapter-type", dbt_adapter_type])
        if dbt_profile:
            args.extend(["--dbt-profile", dbt_profile])
        if dbt_target != "dev":
            args.extend(["--dbt-target", dbt_target])
    if folders:
        args.extend(["--folders", *folders])
    if packages:
        args.extend(["--packages", *packages])
    if dry_run:
        args.append("--dry-run")
    if force:
        args.append("--force")
    target = None
    if output_dir:
        target = str(Path(output_dir).expanduser().resolve() / name)
        args.extend(["--output-dir", str(Path(output_dir).expanduser().resolve())])
    result: dict[str, Any] = {"valid": True, "arguments": args, "target_directory": target}
    if framework == "dbt_analytics":
        result["dbt_setup"] = {
            "adapter": dbt_adapter,
            "adapter_package": dbt_adapter_package or catalog.DBT_ADAPTER_PACKAGES.get(dbt_adapter),
            "profile": dbt_profile or name.replace("-", "_").lower(),
            "target": dbt_target,
            "profiles": ["<project>/.dbt/profiles.yml", "~/.dbt/profiles.yml"],
            "runtime": "Init App creates or reuses the selected project environment, checks dbt-core and the adapter, then runs native dbt init.",
            "commands": [
                "dbt debug --profiles-dir .dbt",
                "dbt deps --profiles-dir .dbt",
                "dbt run --profiles-dir .dbt",
            ],
            "note": "dbt recognizes profiles.yml; user.yml is not a dbt profile file.",
        }
    return result


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
    if framework == "dbt_analytics":
        database = "none"
        database_reason = "dbt connects through the selected warehouse adapter, not --db."

    dbt_adapter = next((
        adapter for adapter, signals in (
            ("snowflake", ("snowflake",)), ("databricks", ("databricks",)),
            ("bigquery", ("bigquery", "google bigquery")), ("redshift", ("redshift",)),
            ("postgres", ("postgres", "postgresql")), ("duckdb", ("duckdb",)),
        ) if any(signal in text for signal in signals)
    ), "duckdb")

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
            "env_manager": "venv",
            **({"dbt_adapter": dbt_adapter} if framework == "dbt_analytics" else {}),
        },
        "recommended_flags": [
            {"flag": "--framework", "value": framework},
            {"flag": "--type", "value": strategy},
            {"flag": "--db", "value": database},
            {"flag": "--venv", "value": "y"},
        ]
        + ([{"flag": "--server", "value": server}] if server else [])
        + ([{"flag": "--drf", "value": True}] if drf else [])
        + ([{"flag": "--dbt-adapter", "value": dbt_adapter}] if framework == "dbt_analytics" else []),
        "reasoning": [framework_reason, database_reason],
        "questions": [
            "What project name should be used?",
            "Which output directory should contain the project?",
        ]
        + (["SQLite was selected as the default. Do you need another database?"] if database == "sqlite" else []),
        "next_step": "Confirm or edit the selection, then call build_init_app_command.",
    }
