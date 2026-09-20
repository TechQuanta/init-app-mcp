# init-app-mcp

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-FastMCP-6B4EFF)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An independent FastMCP server that helps MCP-compatible AI clients understand
the `init-app` CLI and construct valid commands from a user's project needs.

`init-app-mcp` does not import, install, or execute `init-app`. It owns a
versioned capability catalog and returns metadata, recommendations, and command
arguments only. The client or its user decides whether and where to run the
returned command.

## What it does

- Explains the `init-app` command contract and valid flags.
- Lists supported web and specialized project blueprints.
- Converts plain-English requirements into relevant, supported flag choices.
- Validates confirmed choices and returns the exact command arguments.
- Never creates files, starts processes, or runs shell commands.

## Requirements

- Python 3.10 or later
- FastMCP v2 (`fastmcp>=2,<3`)

## Installation

Install from a clone:

```bash
git clone https://github.com/ashmeet07/init-app-mcp.git
cd init-app-mcp
python -m pip install .
```

For development:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## MCP client configuration

Configure an MCP client to use stdio transport:

```json
{
  "mcpServers": {
    "init-app": {
      "command": "init-app-mcp"
    }
  }
}
```

## Horizon Deploy

For Horizon Deploy's repository form, use these values:

| Field | Value |
| --- | --- |
| Server name | `init-app` |
| Entrypoint | `server.py` |
| Requirements | `requirements.txt` |
| Transport | Streamable HTTP |

The root `server.py` is a deployment wrapper that exposes the same `mcp`
server defined by the source package. It exists because Horizon asks for a
Python file path rather than a Python import string. When Horizon runs this
file, it uses Streamable HTTP automatically and honors its `HOST` and `PORT`
environment variables.

If your client requires an absolute Python executable, use:

```json
{
  "mcpServers": {
    "init-app": {
      "command": "/absolute/path/to/python",
      "args": ["-m", "init_app_mcp.server"]
    }
  }
}
```

## Manual diagnostics

The default command starts a stdio MCP server, so it expects JSON-RPC messages
from an MCP client such as VS Code. Do not press Enter after starting it in a
terminal; a blank line is not a valid MCP request.

Use these commands to inspect the installed server manually instead:

```powershell
.\.venv\Scripts\init-app-mcp.exe --list-tools
.\.venv\Scripts\init-app-mcp.exe --metadata
```

To run a local HTTP MCP endpoint for manual client testing, use:

```powershell
.\.venv\Scripts\init-app-mcp.exe --transport streamable-http --port 8001
```

It listens on `http://127.0.0.1:8001/mcp`. Choose another available port if
needed. Keep that terminal open while your
MCP client is connected. Press `Ctrl+C` to stop it.

## Tools

| Tool | Purpose |
| --- | --- |
| `get_init_app_command_metadata` | Returns the CLI contract, flag definitions, allowed values, and recommended workflow. |
| `list_project_blueprints` | Lists all web and specialized project blueprints supported by the catalog. |
| `recommend_init_app_flags` | Maps a user's natural-language requirements to suggested flags, reasoning, and follow-up questions. |
| `build_init_app_command` | Validates user-confirmed options and returns portable `init-app` command arguments. |

## Recommended client workflow

1. Call `get_init_app_command_metadata` to learn the command schema.
2. Call `recommend_init_app_flags` with the user's request.
3. Show the suggested flags and answer any follow-up questions with the user.
4. Call `build_init_app_command` using the confirmed values.
5. Present the final command for the user to run.

Example user request:

```text
I need a production REST API with PostgreSQL, Docker, and Kubernetes.
```

The recommendation tool suggests a selection similar to:

```json
{
  "framework": "fastapi",
  "strategy": "production",
  "database": "postgresql",
  "server": "gunicorn",
  "venv": true
}
```

After the project name and output directory are confirmed, call
`build_init_app_command`. It returns arguments equivalent to:

```bash
init-app billing-api --framework fastapi --type production --db postgresql --venv y --server gunicorn --output-dir ./projects
```

## Development

```bash
python -m pytest
python -m py_compile src/init_app_mcp/server.py src/init_app_mcp/service.py src/init_app_mcp/catalog.py
```

Continuous integration runs this validation on Python 3.10 through 3.13 for
every pull request to `main`.

The project uses a source layout. Its capability catalog lives in
`src/init_app_mcp/catalog.py`; update that catalog and its tests whenever
`init-app` adds or changes CLI capabilities.

## Safety model

This package is intentionally advisory. It does not access a user's project
directory, execute `init-app`, write files, or invoke a shell. A compatible
client must obtain user confirmation before running any recommended command.

## Release checklist

Before releasing a catalog update:

1. Compare `src/init_app_mcp/catalog.py` with the supported `init-app` CLI.
2. Update catalog tests for every new or changed flag or blueprint.
3. Run the development checks above and inspect `--list-tools`.
4. Open a pull request from `feat` to `main` and let CI pass before merging.

## License

Distributed under the [MIT License](LICENSE).
