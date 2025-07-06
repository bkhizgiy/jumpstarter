# Jumpstarter Monorepo - Root Context

## Context Loading Strategy

This file provides base context. More specific context is loaded based on working directory:

- **Root directory**: General monorepo patterns
- **Package directory**: Package-specific patterns + general
- **Driver package**: Driver patterns + package patterns + general

## Base Imports (Always Available)

@.ai-context/uv-monorepo-structure.md
@.ai-context/architecture-overview.md
@.ai-context/development-workflow.md
@.ai-context/testing-patterns.md
@.ai-context/driver-development.md
@.ai-context/driver-categories.md
@.ai-context/grpc-protocol.md
@.ai-context/cli-tools.md
@.ai-context/documentation-authoring.md

## Working Directory Detection

Claude Code automatically discovers nested CLAUDE.md files when you read files in subdirectories.

## Navigation Hints

- `cd packages/jumpstarter/` - Core development context
- `cd packages/jumpstarter-driver-*/` - Driver development context  
- `cd packages/jumpstarter-cli*/` - CLI development context
- `cd packages/jumpstarter-testing/` - Testing framework context
- `cd packages/jumpstarter-protocol/` - Protocol definitions context
- `cd examples/` - Usage examples and patterns

## Monorepo Guidelines

- Each package is independently developed but shares common patterns
- Use `make pkg-test-<package>` for package-specific testing
- Dependencies are managed at workspace level via uv
- Cross-package changes require testing multiple packages

## Quick Reference

### Key Commands

All `make` commands MUST be run in the project root directory.

- `make sync` - Sync all packages and dependencies
- `make build` - Build all packages
- `make test` - Run all tests
- `uv run jmp` - Run Jumpstarter CLI

### Package Structure

- `packages/jumpstarter/` - Core framework
- `packages/jumpstarter-cli*/` - CLI tools
- `packages/jumpstarter-driver-*/` - Hardware drivers
- `packages/jumpstarter-protocol/` - gRPC definitions

### Common Development Tasks

All make commands MUST be run in the root package directory. They cannot be run in driver package directories.

- Create new driver: `make create-driver DRIVER_NAME=my_device DRIVER_CLASS=MyDevice`
- Run tests: `make pkg-test-<package-name>`
- Build docs: `make docs`
- Lint code: `make lint`

## Best Practices and Development Guidelines

### Code Quality Standards

- **Always run linting and type checking**: Use `make lint` and `make ty` before committing
- **Test coverage**: Ensure new code has appropriate test coverage
- **Type hints**: Use type hints for all public APIs and complex functions
- **Docstrings**: All public classes and methods must have comprehensive docstrings
- **Error handling**: Use specific exception types from `jumpstarter.common.exceptions`

### Testing Requirements

- **Test naming**: Use `*_test.py` naming convention for test files
- **Async tests**: Use `@pytest.mark.anyio` for async test functions
- **Mock external dependencies**: Use `unittest.mock.patch` for external services
- **Driver testing**: Use `jumpstarter.common.utils.serve` for driver client testing

### Package Management

- **UV workspace**: Always add new packages to `tool.uv.sources` in root `pyproject.toml`
- **Dependencies**: Declare dependencies in package-specific `pyproject.toml`
- **Entry points**: Register drivers in `[project.entry-points."jumpstarter.drivers"]`
- **Version management**: Use `hatch-vcs` for automatic version management

### Drivers

- **Driver structure**: Follow the standard driver package structure
- **Async methods**: Driver methods should be async when possible
- **Client methods**: Client methods should be sync when possible
- **Configuration**: Use Pydantic dataclasses for driver configuration
- **Resource cleanup**: Implement `close()` method for proper resource management

### Documentation

- **MyST markdown**: Use MyST syntax for documentation files
- **Code examples**: Include working code examples in documentation
- **API documentation**: Auto-generate API docs from docstrings
- **Configuration examples**: Provide example YAML configurations

### Common Patterns

- **Error messages**: Include context and actionable information
- **Logging**: Use appropriate log levels for debugging
- **Configuration validation**: Validate configuration early with clear error messages
- **Backwards compatibility**: Maintain API compatibility across minor versions

### Security Considerations

- **No secrets in code**: Never hardcode credentials or API keys
- **Input validation**: Validate all external inputs
- **Secure defaults**: Use secure default configurations
- **Access control**: Implement proper authentication and authorization

### Performance Guidelines

- **Async I/O**: Use async/await for all I/O operations
- **Connection pooling**: Reuse connections where possible
- **Resource efficiency**: Clean up resources promptly
- **Streaming**: Use streaming for large data transfers

For detailed information on any topic, refer to the specific files referenced above.
