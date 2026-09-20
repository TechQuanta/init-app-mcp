import json

from init_app_mcp import __version__
from init_app_mcp import service
from init_app_mcp.server import TOOL_NAMES, main, mcp


EXPECTED_TOOLS = {
    "build_init_app_command",
    "get_init_app_command_metadata",
    "list_tool_domains",
    "select_domain_tools",
    "list_project_blueprints",
    "recommend_init_app_flags",
}


def test_server_registers_the_documented_tools():
    assert set(TOOL_NAMES) == EXPECTED_TOOLS


def test_list_tools_diagnostic_is_valid_json(capsys):
    main(["--list-tools"])
    output = json.loads(capsys.readouterr().out)
    assert output == {"server": "init-app", "tools": sorted(EXPECTED_TOOLS)}


def test_metadata_diagnostic_matches_library_version(capsys):
    main(["--metadata"])
    output = json.loads(capsys.readouterr().out)
    assert output["version"] == __version__
    assert output["command"] == service.command_metadata()["command"]
