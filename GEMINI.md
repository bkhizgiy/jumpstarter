# Jumpstarter Monorepo - Gemini Context

## Context Loading Strategy

This file provides base context for Google Gemini. More specific context is loaded based on working directory:

- **Root directory**: General monorepo patterns and architecture
- **Package directory**: Package-specific patterns + general context
- **Driver package**: Driver patterns + package patterns + general context

## Working Directory Detection

When working in specific directories, additional relevant context becomes available:

## Navigation Hints for Context Loading

- `cd packages/jumpstarter/` - Core framework development context
- `cd packages/jumpstarter-driver-*/` - Hardware driver development context  
- `cd packages/jumpstarter-cli*/` - CLI tool development context
- `cd packages/jumpstarter-testing/` - Testing framework context
- `cd packages/jumpstarter-protocol/` - gRPC protocol definitions context

## Project Overview

Jumpstarter is a Hardware-in-the-Loop (HiL) testing framework that enables:

- Unified testing across local, virtual, and remote hardware
- Hardware abstraction through pluggable drivers
- Collaborative testing with shared hardware resources
- CI/CD integration for automated testing

## Key Architecture Components

### Project Structure

```
jumpstarter/
├── packages/jumpstarter/               # Core framework
├── packages/jumpstarter-cli*/          # CLI tools (jmp, j)
├── packages/jumpstarter-driver-*/      # Hardware drivers
├── packages/jumpstarter-protocol/      # gRPC definitions
├── packages/jumpstarter-kubernetes/    # Distributed mode
└── examples/                           # Example projects
```

### Core Concepts

- **Drivers**: Hardware abstraction layer (power, serial, network, etc.)
- **Exporters**: Manage drivers and expose via gRPC
- **Clients**: Libraries and CLI tools for device interaction
- **Service**: Kubernetes controller for distributed resource management

## Technology Stack

- **Language**: Python 3.11+
- **Package Manager**: UV with monorepo structure
- **Communication**: gRPC with Protocol Buffers
- **Testing**: pytest with async support
- **Documentation**: Sphinx with MyST markdown

## Development Commands

**Package Management** (run from root):

```bash
make sync          # Sync all packages
make build         # Build all packages
make test          # Run all tests
uv run jmp         # Run CLI
```

**Driver Development**:

```bash
make create-driver DRIVER_NAME=my_device DRIVER_CLASS=MyDevice
make pkg-test-jumpstarter-driver-my-device
```

**Code Quality**:

```bash
make lint          # Lint code
make ty            # Type checking
make docs          # Build documentation
```

## Driver Development Patterns

### Driver Structure

```python
from jumpstarter.driver import Driver, export
from pydantic.dataclasses import dataclass

@dataclass(kw_only=True)
class MyDevice(Driver):
    host: str
    port: int = 8080
    
    @classmethod
    def client(cls) -> str:
        return "my_driver.client.MyDeviceClient"
    
    @export
    async def power_on(self) -> None:
        # Implementation
        pass
```

### Client Interface

```python
from jumpstarter.client import DriverClient

class MyDeviceClient(DriverClient):
    def power_on(self) -> None:
        self.call("power_on")
```

### Configuration

```yaml
# exporter.yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: my-device
export:
  power:
    type: my_driver.driver.MyDevice
    config:
      host: "192.168.1.100"
      port: 8080
```

## Testing Patterns

### Driver Testing

```python
import pytest
from jumpstarter.common.utils import serve

@pytest.mark.anyio
async def test_power_cycle():
    driver = MyDevice(host="test.com")
    await driver.power_on()
    assert await driver.is_powered()

def test_client():
    instance = MyDevice(host="test.com")
    with serve(instance) as client:
        client.power_on()
```

### Test Conventions

- Test files: `*_test.py`
- Async tests: `@pytest.mark.anyio`
- Use `unittest.mock.patch` for mocking
- Driver client testing: `jumpstarter.common.utils.serve`

## Package Management

### UV Workspace

- All packages defined in root `pyproject.toml`
- Package-specific dependencies in package `pyproject.toml`
- Entry points for driver registration

### Adding New Packages

```toml
# root pyproject.toml
[tool.uv.sources]
new-package = { workspace = true }
```

### Driver Entry Points

```toml
# package pyproject.toml
[project.entry-points."jumpstarter.drivers"]
MyDevice = "my_driver.driver:MyDevice"
```

## CLI Usage

### Main Commands

```bash
# Configuration
jmp config client create prod --endpoint https://jumpstarter.dev
jmp config exporter create lab --config device.yaml

# Interactive shell
jmp shell --exporter lab-device
jmp shell -l type=rpi,env=dev    # Distributed mode

# Resource management
jmp create lease --selector vendor=acme --duration 1h
jmp get exporters
jmp delete lease <id>
```

### Inside jmp shell

```python
# Use 'j' command for driver interaction
j.power.on()
j.serial.write(b"hello\n")
```

## Common Driver Categories

### Power Control

- energenie, yepkit, tasmota
- Methods: `on()`, `off()`, `cycle()`, `read()`

### Communication

- pyserial, uboot, http, shell
- Serial, network, custom protocols

### Storage

- tftp, opendal, sdwire
- File transfer, disk imaging

### Debug/Development

- probe-rs, qemu, raspberrypi
- Hardware debugging, virtualization

## Best Practices

### Code Quality

- Always use type hints
- Comprehensive docstrings
- Specific exception types
- Proper async/await usage

### Configuration

- Use Pydantic dataclasses
- Validate early with clear errors
- Secure defaults
- No hardcoded secrets

### Documentation

- MyST markdown syntax
- Working code examples
- Auto-generated API docs
- Configuration examples

## Error Handling

```python
from jumpstarter.common.exceptions import DriverError

try:
    await device.connect()
except ConnectionError as e:
    raise DriverError(f"Connection failed: {e}") from e
```

## Security Guidelines

- Never hardcode credentials
- Validate all external inputs
- Use secure default configurations
- Implement proper authentication

This context should help you understand the Jumpstarter framework and assist with development, testing, and documentation tasks.
