import pytest

from init_app_mcp import service


def test_blueprints_include_web_and_mcp():
    ids = {item["id"] for item in service.list_blueprints()}
    assert {"fastapi", "django", "mcp"} <= ids


def test_preview_has_no_side_effect_and_returns_arguments(tmp_path):
    result = service.project_command_preview(
        "sample_api", framework="fastapi", output_dir=str(tmp_path)
    )
    assert result["valid"] is True
    assert result["arguments"][:4] == ["init-app", "sample_api", "--framework", "fastapi"]
    assert not (tmp_path / "sample_api").exists()


def test_preview_rejects_invalid_framework():
    with pytest.raises(ValueError, match="Unsupported framework"):
        service.project_command_preview("sample", framework="rails")


def test_command_metadata_has_the_required_cli_contract():
    metadata = service.command_metadata()
    flags = {flag["name"] for flag in metadata["flags"]}
    assert metadata["command"] == "init-app <project_name>"
    assert {"--framework", "--type", "--db", "--venv", "--env-manager", "--spec", "--dry-run", "--force", "--app-name"} <= flags


def test_uv_preview_uses_the_uv_manager_flag():
    result = service.project_command_preview("uv_api", env_manager="uv")
    assert result["arguments"][-2:] == ["--env-manager", "uv"]


def test_dbt_preview_selects_snowflake_and_user_profile():
    result = service.project_command_preview(
        "finance_transform",
        framework="dbt_analytics",
        database="none",
        dbt_adapter="snowflake",
        dbt_profile="finance",
    )
    assert "--db" not in result["arguments"]
    assert result["arguments"][-4:] == ["--dbt-adapter", "snowflake", "--dbt-profile", "finance"]
    assert result["dbt_setup"]["profiles"] == ["<project>/.dbt/profiles.yml", "~/.dbt/profiles.yml"]


def test_dbt_preview_accepts_any_compatible_custom_adapter():
    result = service.project_command_preview(
        "warehouse",
        framework="dbt_analytics",
        dbt_adapter="custom",
        dbt_adapter_package="dbt-acme",
        dbt_adapter_type="acme",
    )
    assert "--dbt-adapter-package" in result["arguments"]


def test_domain_selection_supports_multiple_resume_tools():
    result = service.select_domain_tools("resume", ["build_resume", "improve_bullets"])
    assert result["selected_tools"] == ["build_resume", "improve_bullets"]


def test_domain_selection_rejects_unknown_tools():
    with pytest.raises(ValueError, match="Unsupported tools"):
        service.select_domain_tools("code", ["build_resume"])


def test_preview_supports_new_custom_and_safe_review_options():
    result = service.project_command_preview(
        "sample_api", strategy="custom", app_name="api", folders=["src/api", "tests"],
        packages=["src/api"], spec_path="project.json", dry_run=True,
    )
    assert result["arguments"] == [
        "init-app", "sample_api", "--framework", "fastapi", "--type", "custom",
        "--spec", "project.json", "--db", "sqlite", "--venv", "y",
        "--app-name", "api", "--folders", "src/api", "tests", "--packages", "src/api", "--dry-run",
    ]


def test_preview_rejects_unsafe_custom_paths():
    with pytest.raises(ValueError, match="unsafe path"):
        service.project_command_preview("sample", strategy="custom", folders=["../outside"])


def test_recommendation_maps_requirement_to_supported_flags():
    result = service.recommend_flags("A production REST API with PostgreSQL, Docker, and Kubernetes.")
    assert result["selection"] == {
        "framework": "fastapi",
        "strategy": "production",
        "database": "postgresql",
        "server": "gunicorn",
        "drf": False,
        "venv": True,
        "env_manager": "venv",
    }
    assert {item["flag"] for item in result["recommended_flags"]} >= {"--framework", "--type", "--db"}


def test_recommendation_maps_django_rest_to_drf():
    result = service.recommend_flags("A Django admin site with REST API endpoints.")
    assert result["selection"]["framework"] == "django"
    assert result["selection"]["drf"] is True
    assert {item["flag"] for item in result["recommended_flags"]} >= {"--drf"}


def test_recommendation_recognizes_explicit_fastapi():
    result = service.recommend_flags("Create a FastAPI service.")
    assert result["selection"]["framework"] == "fastapi"
    assert "fastapi" in result["reasoning"][0]


def test_server_metadata_is_independent_of_init_app_package():
    metadata = service.library_metadata()
    assert metadata["name"] == "init-app-mcp"
    assert metadata["target_cli"] == "init-app"
    assert "does not create files" in metadata["safety"]
