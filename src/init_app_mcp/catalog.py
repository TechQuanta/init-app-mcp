"""Static init-app capability catalog owned by the MCP server.

Keep this module independent of the ``init-app`` Python package. Update it
when init-app publishes a new blueprint or CLI option.
"""

from __future__ import annotations

from typing import Any


INIT_APP_VERSION = "3.2.0"
STRATEGIES = ("standard", "production", "auto_config", "custom")
DATABASES = ("postgresql", "mysql", "sqlite", "mongodb", "none")

COMMAND_FLAGS = (
    {"name": "--framework", "required": True, "values_from": "blueprints", "description": "Project blueprint."},
    {"name": "--spec", "required": False, "value": "FILE", "description": "JSON project specification; explicit flags override its values."},
    {"name": "--dry-run", "required": False, "description": "Validate and print the resolved configuration without writing files."},
    {"name": "--force", "required": False, "description": "Allow generation into an existing project directory."},
    {"name": "--type", "required": False, "default": "standard", "values": STRATEGIES, "description": "Build strategy."},
    {"name": "--db", "required": False, "default": "sqlite", "values": DATABASES, "description": "Database engine."},
    {"name": "--server", "required": False, "values_from": "selected blueprint", "description": "Runtime server."},
    {"name": "--venv", "required": False, "default": "y", "values": ("y", "n"), "description": "Create a virtual environment (legacy option)."},
    {"name": "--env-manager", "required": False, "default": "venv", "values": ("venv", "uv", "none"), "description": "Choose the environment and dependency manager."},
    {"name": "--app-name", "required": False, "value": "PYTHON_IDENTIFIER", "description": "Application package name (default: core_app)."},
    {"name": "--folders", "required": False, "only_for": "custom", "value": "RELATIVE_PATH [RELATIVE_PATH ...]", "description": "Custom project folders."},
    {"name": "--packages", "required": False, "only_for": "custom", "value": "RELATIVE_PATH [RELATIVE_PATH ...]", "description": "Folders that receive __init__.py; each must be in --folders."},
    {"name": "--drf", "required": False, "only_for": "django", "description": "Enable Django REST Framework."},
    {"name": "--output-dir", "required": False, "description": "Parent directory for the generated project."},
)

BLUEPRINTS: dict[str, dict[str, Any]] = {
    "fastapi": {
        "kind": "web",
        "description": "High-performance asynchronous API with OpenAPI support.",
        "servers": ("uvicorn", "gunicorn"),
    },
    "flask": {
        "kind": "web",
        "description": "Flexible, lightweight WSGI web application.",
        "servers": ("gunicorn", "waitress", "gevent", "wsgiref", "na"),
    },
    "django": {
        "kind": "web",
        "description": "Batteries-included web application; supports Django REST Framework.",
        "servers": ("gunicorn", "waitress", "wsgiref"),
    },
    "bottle": {"kind": "web", "description": "Minimal single-file WSGI application.", "servers": ("waitress", "gevent", "wsgiref", "na")},
    "sanic": {"kind": "web", "description": "Async Python web server.", "servers": ("na",)},
    "falcon": {"kind": "web", "description": "Minimal high-performance ASGI/WSGI API.", "servers": ("gunicorn", "waitress", "wsgiref")},
    "tornado": {"kind": "web", "description": "Asynchronous networking application.", "servers": ("na",)},
    "pyramid": {"kind": "web", "description": "Flexible Python web application.", "servers": ("waitress", "gunicorn")},
    "base": {"kind": "specialized", "description": "General Python project.", "servers": ("na",)},
    "hp_cli": {"kind": "specialized", "description": "High-performance command-line application.", "servers": ("na",)},
    "data_pipeline": {"kind": "specialized", "description": "ETL and workflow orchestration project.", "servers": ("na",)},
    "dbt_analytics": {"kind": "specialized", "description": "dbt analytics project.", "servers": ("na",)},
    "mlops_core": {"kind": "specialized", "description": "ML lifecycle and model-serving project.", "servers": ("na",)},
    "rag_ai": {"kind": "specialized", "description": "Retrieval-augmented generation project.", "servers": ("na",)},
    "mcp": {"kind": "specialized", "description": "MCP tool hub project.", "servers": ("na",)},
}

TOOL_DOMAINS: dict[str, dict[str, Any]] = {
    "research": {
        "description": "Investigate, compare, evaluate, and summarize information.",
        "tools": ("compare_sources", "explain_topic", "evaluate_claims", "summarize_research"),
    },
    "writing": {
        "description": "Draft, rewrite, structure, and adapt written content.",
        "tools": ("draft_content", "rewrite_text", "write_email", "create_article"),
    },
    "resume": {
        "description": "Build and tailor resumes, bullets, and application materials.",
        "tools": ("build_resume", "tailor_resume", "improve_bullets", "write_cover_letter"),
    },
    "code": {
        "description": "Write, debug, review, refactor, and explain software.",
        "tools": ("write_code", "debug_code", "review_code", "refactor_code", "explain_code"),
    },
    "init-app": {
        "description": "Create and configure Python project blueprints.",
        "tools": ("get_init_app_command_metadata", "list_project_blueprints", "recommend_init_app_flags", "build_init_app_command"),
    },
}


def list_blueprints() -> list[dict[str, Any]]:
    """Return MCP-ready metadata for every supported init-app blueprint."""
    return [
        {
            "id": identifier,
            **details,
            "servers": list(details["servers"]),
            "strategies": list(STRATEGIES),
            "databases": list(DATABASES),
        }
        for identifier, details in BLUEPRINTS.items()
    ]


def command_metadata() -> dict[str, Any]:
    """Describe the init-app command contract without importing init-app."""
    return {
        "command": "init-app <project_name>",
        "project_name": {"pattern": "^[A-Za-z][A-Za-z0-9_-]{0,63}$"},
        "flags": [
            {key: list(value) if isinstance(value, tuple) else value for key, value in flag.items()}
            for flag in COMMAND_FLAGS
        ],
    }


def list_tool_domains() -> list[dict[str, Any]]:
    """Return parent domains and their selectable child tools."""
    return [
        {"id": domain, "description": details["description"], "tools": list(details["tools"])}
        for domain, details in TOOL_DOMAINS.items()
    ]
