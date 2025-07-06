# Development Workflow and Project Structure

This document outlines the development workflow, contribution process, and project organization for Jumpstarter development.

## Project Organization

### Repository Structure

```text
jumpstarter/
├── .ai-context/                    # AI context documentation
├── __templates__/                  # Code generation templates
│   ├── create_driver.sh           # Driver creation script
│   └── driver/                    # Driver templates
├── docs/                          # Sphinx documentation
├── examples/                      # Example projects and demos
├── packages/                      # Monorepo packages
│   ├── jumpstarter/               # Core framework
│   ├── jumpstarter-cli*/          # CLI tools
│   ├── jumpstarter-driver-*/      # Hardware drivers
│   ├── jumpstarter-kubernetes/    # Kubernetes integration
│   └── jumpstarter-protocol/      # gRPC definitions
├── Makefile                       # Build automation
├── pyproject.toml                 # Workspace configuration
└── uv.lock                        # Dependency lock file
```

### Package Categories

#### Core Framework

- **`jumpstarter`**: Core framework and base classes
- **`jumpstarter-protocol`**: Python gRPC protocol definitions generated from the [Jumpstarter Protocol](https://github.com/jumpstarter-dev/jumpstarter-protocol) repository
- **`jumpstarter-testing`**: Testing integration for writing tests that use Jumpstarter in pytest

#### CLI Packages

- **`jumpstarter-cli`**: Main user-facing CLI (`jmp` for general commands, `j` for driver commands within shell sessions)
- **`jumpstarter-cli-admin`**: Administrative commands for managing the Jumpstarter Service
- **`jumpstarter-cli-driver`**: Experimental driver package management CLI
- **`jumpstarter-cli-common`**: Shared CLI utilities

#### Hardware Drivers

- **`jumpstarter-driver-*`**: Driver Packages
  - Categories: power, communication, storage, debug, virtualization
  - Examples: energenie, pyserial, qemu, probe-rs

#### Infrastructure

- **`jumpstarter-kubernetes`**: Python Kubernetes API definitions and functions for managing the Jumpstarter Service
- **`jumpstarter-imagehash`**: Image comparison utilities
- **`hatch-pin-jumpstarter`**: Build system integration

## Development Environment Setup

### Prerequisites

- **Python**: 3.11 or higher
- **UV Package Manager**: Latest version
- **Docker**: For containerized testing
- **Kubernetes**: For distributed mode development (optional)

### Quick Setup

```bash
# Clone repository
git clone https://github.com/jumpstarter-dev/jumpstarter.git
cd jumpstarter

# Install dependencies
make sync

# Verify installation
uv run jmp --help
```

### Development Tools

#### Package Manager (UV) and Makefile

```bash
# Sync all packages and dependencies
make sync

# Build all packages
make build

# Clean build artifacts
make clean
```

#### Testing

```bash
# Run all tests
make test

# Test a specific package
make pkg-test-jumpstarter-driver-shell

# Run type checking
make ty
```

#### Code Quality

```bash
# Lint code
make lint

# Auto-fix linting issues
make lint-fix

# Type checking
make pkg-ty-all
```

## Development Workflow

### 1. Feature Development

#### Driver Development

```bash
# Create new driver
make create-driver DRIVER_NAME=my_device DRIVER_CLASS=MyDevice

# Implement driver logic
# Edit packages/jumpstarter-driver-my-device/jumpstarter_driver_my_device/driver.py
# Edit packages/jumpstarter-driver-my-device/jumpstarter_driver_my_device/client.py

# Test driver
make pkg-test-jumpstarter-driver-my-device

# Verify integration with CLI tools
uv run jmp shell --exporter-config ./packages/jumpstarter-driver-my-device/examples/exporter.yaml
```

### 2. Testing Strategy

#### Unit Testing

```python
# Driver unit tests
@pytest.mark.anyio
async def test_power_cycle():
    config = {"host": "localhost", "port": 8080}
    driver = MyDevice(config)

    await driver.power_on()
    assert await driver.is_powered()

    await driver.power_off()
    assert not await driver.is_powered()
```

### 3. Documentation

#### Code Documentation

- **Docstrings**: All public APIs must have comprehensive docstrings
- **Type Hints**: Use type hints for better IDE support and documentation
- **Examples**: Include usage examples in docstrings

#### User Documentation

```bash
# Build documentation
make docs

# Serve documentation locally
make docs-serve
```

#### API Documentation

- **Driver APIs**: Document all driver methods and configuration options
- **CLI Usage**: Include examples for all CLI commands
- **Protocol Documentation**: gRPC service definitions and message formats

### 4. Code Review Process

#### Pull Request Guidelines

1. **Clear Description**: Explain what the change does and why
2. **Test Coverage**: Include appropriate tests for new functionality
3. **Documentation**: Update documentation for user-facing changes
4. **Breaking Changes**: Clearly mark and document breaking changes

#### Review Checklist

- [ ] Code follows project style guidelines
- [ ] Tests pass and provide adequate coverage
- [ ] Documentation is updated
- [ ] No security vulnerabilities introduced
- [ ] Performance impact considered
- [ ] Backward compatibility maintained (unless breaking change)

## Code Style and Standards

### Python Code Style

#### Formatting

- **Tool**: Ruff for linting and formatting
- **Line Length**: 120 characters maximum
- **Import Sorting**: Automatic via ruff

#### Type Hints

```python
from typing import Optional, Dict, List
import asyncio

async def power_control(
    device_id: str,
    action: str,
    timeout: Optional[int] = None
) -> Dict[str, any]:
    """Control device power state.

    Args:
        device_id: Unique device identifier
        action: Power action ('on', 'off', 'cycle')
        timeout: Operation timeout in seconds

    Returns:
        Status information dictionary

    Raises:
        DeviceError: If power operation fails
        TimeoutError: If operation exceeds timeout
    """
    pass
```

#### Error Handling

```python
# Use specific exception types
from jumpstarter.common.exceptions import DriverError, ConfigurationError

# Provide helpful error messages
raise DriverError(
    f"Failed to connect to device {device_id}: {error_details}"
)

# Chain exceptions for debugging
try:
    await device.connect()
except ConnectionError as e:
    raise DriverError(f"Connection failed: {e}") from e
```

### Configuration Patterns

#### Driver Configuration

```python
from pydantic import BaseModel, Field

class MyDeviceConfig(BaseModel):
    """Configuration for MyDevice driver."""

    host: str = Field(..., description="Device hostname or IP")
    port: int = Field(8080, description="Device port number")
    timeout: int = Field(30, description="Connection timeout in seconds")
    retries: int = Field(3, description="Number of connection retries")

    class Config:
        extra = "forbid"  # Reject unknown configuration keys
```

#### CLI Configuration

```yaml
# ~/.jumpstarter/client.yaml
current_client: production
clients:
  production:
    endpoint: https://jumpstarter.company.com
    auth:
      type: oidc
      provider: corporate-sso
  development:
    endpoint: https://jumpstarter-dev.company.com
    auth:
      type: token
      token_file: ~/.jumpstarter/dev-token
```

## Release Process

### Version Management

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Version Source**: Git tags via hatch-vcs
- **Changelog**: Automated generation from commit messages

## Contributing Guidelines

### Getting Started

1. **Fork Repository**: Create personal fork for development
2. **Setup Environment**: Follow development environment setup
3. **Find Issues**: Look for "good first issue" labels
4. **Join Community**: Matrix chat and weekly meetings

### Contribution Types

#### Bug Fixes

- **Issue First**: Create issue describing the bug
- **Small Changes**: Fix can be made directly
- **Large Changes**: Discuss approach in issue first

#### New Features

- **RFC Process**: Large features may require RFC document
- **Design Discussion**: Use GitHub discussions for design talks
- **Prototype**: Consider creating prototype for complex features

#### Documentation

- **User Docs**: Help improve user-facing documentation
- **Code Comments**: Improve code readability
- **Examples**: Add real-world usage examples

### Community

#### Communication Channels

- **Matrix Chat**: #jumpstarter:matrix.org
- **GitHub Discussions**: Design discussions and Q&A
- **Weekly Meetings**: Community calls every Tuesday

#### Code of Conduct

- **Inclusive Environment**: Welcoming to all experience levels
- **Respectful Communication**: Professional and constructive
- **Collaborative Development**: Help others learn and grow
