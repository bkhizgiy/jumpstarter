# GitHub Copilot Instructions for Jumpstarter

This file provides GitHub Copilot and VS Code with context about the Jumpstarter project structure and development patterns.

## Project Overview

Jumpstarter is an open-source Hardware-in-the-Loop (HiL) testing framework built with:

- **Python 3.11+** with async/await patterns
- **UV package manager** with monorepo structure
- **gRPC communication** for all service interactions
- **Pydantic** for configuration and data validation
- **pytest** with async support for testing

## Code Generation Guidelines

### Driver Development

When creating new drivers, follow these patterns:

```python
# Driver class template
from jumpstarter.driver import Driver, export
from pydantic.dataclasses import dataclass

@dataclass(kw_only=True)
class MyDevice(Driver):
    host: str
    port: int = 8080
    
    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_mydevice.client.MyDeviceClient"
    
    @export
    async def power_on(self) -> None:
        """Power on the device."""
        # Implementation here
        pass
```

```python
# Client class template
from jumpstarter.client import DriverClient

class MyDeviceClient(DriverClient):
    def power_on(self) -> None:
        """Power on the device."""
        self.call("power_on")
```

### Configuration Patterns

Always use Pydantic for configuration:

```python
from pydantic import BaseModel, Field

class DeviceConfig(BaseModel):
    host: str = Field(..., description="Device hostname")
    port: int = Field(8080, description="Device port")
    timeout: int = Field(30, description="Connection timeout")
```

### Testing Patterns

Use these testing conventions:

```python
import pytest
from jumpstarter.common.utils import serve

# Async driver tests
@pytest.mark.anyio
async def test_power_cycle():
    driver = MyDevice(host="test.com")
    await driver.power_on()
    assert await driver.is_powered()

# Client tests with serve utility
def test_client():
    instance = MyDevice(host="test.com")
    with serve(instance) as client:
        client.power_on()
```

## Project Structure

```
packages/
├── jumpstarter/                    # Core framework
│   ├── client/                     # Client libraries
│   ├── driver/                     # Driver base classes
│   ├── exporter/                   # Exporter implementation
│   └── common/                     # Shared utilities
├── jumpstarter-cli*/               # CLI tools
├── jumpstarter-driver-*/           # Hardware drivers
├── jumpstarter-protocol/           # gRPC definitions
└── jumpstarter-testing/            # Testing utilities
```

## Key Commands

```bash
# Package management (from root)
make sync           # Sync all packages
make build          # Build all packages
make test           # Run all tests

# Driver development
make create-driver DRIVER_NAME=my_device DRIVER_CLASS=MyDevice
make pkg-test-jumpstarter-driver-my-device

# Code quality
make lint           # Lint code
make ty             # Type checking
```

## Common Import Patterns

```python
# Core imports
from jumpstarter.driver import Driver, export
from jumpstarter.client import DriverClient
from jumpstarter.common.exceptions import DriverError

# Configuration
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass

# Testing
import pytest
from jumpstarter.common.utils import serve

# Async utilities
import asyncio
import anyio
```

## Error Handling

Always use specific exceptions:

```python
from jumpstarter.common.exceptions import DriverError, ConfigurationError

try:
    await device.connect()
except ConnectionError as e:
    raise DriverError(f"Connection failed: {e}") from e
```

## Documentation Standards

Use comprehensive docstrings:

```python
async def power_on(self, timeout: Optional[int] = None) -> bool:
    """Turn on device power.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        DriverError: If power operation fails
        TimeoutError: If operation times out
    """
```

## Package Registration

Register drivers in pyproject.toml:

```toml
[project.entry-points."jumpstarter.drivers"]
MyDevice = "jumpstarter_driver_mydevice.driver:MyDevice"
```

## Configuration Examples

Exporter configuration:

```yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: my-device
export:
  power:
    type: jumpstarter_driver_mydevice.driver.MyDevice
    config:
      host: "192.168.1.100"
      port: 8080
```

## Best Practices

1. **Async First**: Use async/await for all I/O operations
2. **Type Safety**: Include type hints for all function parameters
3. **Error Context**: Provide actionable error messages
4. **Resource Cleanup**: Implement proper cleanup in drivers
5. **Testing**: Write both unit and integration tests
6. **Documentation**: Include examples in docstrings

## Common Patterns

### Driver with Composite Children

```python
def __post_init__(self):
    if hasattr(super(), "__post_init__"):
        super().__post_init__()
    self.children["power"] = PowerDriver(parent=self)
```

### Client CLI Integration

```python
def cli(self):
    @click.group()
    def base():
        """My Device CLI"""
        pass
    
    @base.command()
    def status():
        """Check device status"""
        print(self.get_status())
    
    return base
```

This context should help Copilot generate code that follows Jumpstarter conventions and patterns.
