# Contributing

Thank you for considering contributing to the SunGather charm!

## Development Setup

To make contributions to this charm, you'll need a working development setup.

### Prerequisites

- Python 3.10 or later
- [Charmcraft](https://documentation.ubuntu.com/charmcraft/) installed
- [Juju](https://juju.is/docs) installed and configured
- A Kubernetes cluster for testing (or use [MicroK8s](https://microk8s.io/))

### Setting Up the Development Environment

You can create an environment for development with `tox`:

```shell
tox devenv -e integration
source venv/bin/activate
```

Alternatively, you can use `uv` for faster dependency installation:

```shell
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Optional: Using Concierge

For a complete development environment, you can use [concierge](https://github.com/canonical/concierge):

```shell
sudo snap install concierge
concierge prepare -p dev
```

This will set up a local Juju controller with MicroK8s.

## Testing

This project uses `tox` for managing test environments. There are pre-configured environments for different types of tests:

```shell
tox run -e format        # Format code according to style rules
tox run -e lint          # Check code style with ruff
tox run -e unit          # Run unit tests
tox run -e integration   # Run integration tests
tox                      # Run format, lint, and unit tests
```

### Unit Tests

Unit tests use the `ops.testing` framework to test charm logic without requiring a Juju controller.

Run unit tests:

```shell
tox run -e unit
```

Or with pytest directly:

```shell
pytest tests/unit/
```

### Integration Tests

Integration tests use Jubilant to test the charm on a real Juju controller.

Before running integration tests, ensure you have:
1. A Juju controller set up
2. Built the charm: `charmcraft pack`

Run integration tests:

```shell
tox run -e integration
```

Or with pytest directly:

```shell
pytest tests/integration/
```

#### Mock Sungrow Server

The integration tests include a mock Sungrow inverter server that simulates both Modbus TCP and HTTP/WebSocket protocols. This allows testing the charm with a working workload without requiring actual hardware.

The mock server is automatically started by the `mock_sungrow` pytest fixture. Tests in `test_charm_with_mock.py` use this fixture to verify that the charm works correctly when the workload can actually connect to an inverter.

The original tests in `test_charm.py` verify that the charm handles broken workloads gracefully (using the default OCI image with missing dependencies).

See [tests/integration/mock_sungrow/README.md](tests/integration/mock_sungrow/README.md) for more details about the mock server implementation.

## Building the Charm

Build the charm using charmcraft:

```shell
charmcraft pack
```

After building, analyse the charm for potential issues:

```shell
charmcraft analyse *.charm
```

## Code Style Guidelines

This project follows these code style guidelines:

### General Python Style

- Use `import module` rather than `from module import thing` (except for typing imports)
- Use absolute imports
- Use British English for comments and documentation
- Use modern type annotations (`x | y | None` instead of `Optional[Union[x, y]]`)
- Add `from __future__ import annotations` when needed

### Charm-Specific Guidelines

- Keep the amount of code in `try`/`except` blocks as small as possible
- Never catch `Exception` - catch specific exceptions
- Use absolute paths in subprocesses
- Do not execute processes via a shell
- Configuration dataclasses should be defined for charm config
- Action dataclasses should be defined for each action
- The `src/charm.py` file should contain the charm class and event handlers
- The `src/sungather.py` file should contain workload interaction functions

See [Ops Style Guide](https://github.com/canonical/operator/blob/main/STYLE.md) for more details.

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions or changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

Example:
```
feat: add MQTT authentication support

- Add support for MQTT username and password via Juju secrets
- Update configuration validation to check for credentials
```

## Pull Request Process

1. Fork the repository and create your branch from `main`
2. Make your changes, following the code style guidelines
3. Add or update tests as appropriate
4. Update documentation (README, TUTORIAL, etc.) if needed
5. Update CHANGELOG.md under the `[Unreleased]` section
6. Ensure all tests pass: `tox`
7. Commit your changes with clear, conventional commit messages
8. Push to your fork and submit a pull request

### Pull Request Checklist

- [ ] Tests pass locally
- [ ] Code follows the style guidelines
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages follow conventional commits format

## Pre-commit Hooks

We recommend setting up pre-commit hooks to automatically check your code before committing:

```shell
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

The pre-commit configuration will run:
- Standard pre-commit checks (trailing whitespace, file endings, etc.)
- Ruff format check
- Ruff linting

## Reporting Bugs

When reporting bugs, please include:

- Steps to reproduce the issue
- Expected behaviour
- Actual behaviour
- Environment details (Juju version, Kubernetes version, charm version)
- Relevant logs from `juju debug-log`

## Requesting Features

When requesting features:

- Describe the feature and its use case
- Explain why this feature would be useful
- Provide examples of how it would be used

## Security Issues

Please do not report security vulnerabilities through public GitHub issues. Instead, see [SECURITY.md](SECURITY.md) for instructions on responsible disclosure.

## Questions

If you have questions about contributing, feel free to:

- Open a discussion on GitHub
- Ask in the Juju community channels
- Review the [Juju documentation](https://juju.is/docs)

## Licence

By contributing, you agree that your contributions will be licensed under the Apache Licence 2.0.
