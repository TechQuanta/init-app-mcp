# Contributing

Please submit focused pull requests against `main`. Install development
dependencies with `python -m pip install -e ".[dev]"`, then run
`python -m pytest` before opening a pull request.

The server must remain independent of the `init-app` package: update the static
catalog and tests whenever the public init-app CLI changes. Contributions are
distributed under the repository's MIT License.
