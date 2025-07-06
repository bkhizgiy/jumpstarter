# Driver Development Guide

Drivers are the core abstraction layer in Jumpstarter that provide standardized interfaces to hardware devices. This guide covers the patterns, conventions, and best practices for developing Jumpstarter drivers.

## Driver Structure

### Package Organization

Each driver follows a consistent structure:

```text
packages/jumpstarter-driver-{name}/
├── README.md                           # Driver documentation
├── pyproject.toml                      # Package configuration
├── examples/
│   └── exporter.yaml                   # Example configuration
└── jumpstarter_driver_{name}/
    ├── __init__.py                     # Package initialization
    ├── client.py                       # Client-side interface
    ├── client_test.py                  # Client unit tests
    ├── driver.py                       # Core driver implementation
    └── driver_test.py                  # Driver unit tests
```

### Naming Conventions

- **Package names**: `jumpstarter-driver-{name}` (kebab-case)
- **Module names**: `jumpstarter_driver_{name}` (snake_case)
- **Class names**: PascalCase (e.g., `MyDevice`, `UsbCamera`)

## Core Driver Components

### 1. Driver Class (`driver.py`)

The main driver implementation that manages hardware communication:

```python
from collections.abc import AsyncGenerator
from dataclasses import field
from pydantic.dataclasses import dataclass

from jumpstarter.driver import Driver
from jumpstarter.driver.decorators import export


# We use the Pydantic `@dataclass` decorator
@dataclass(kw_only=True)
class MyDevice(Driver):
    """Driver for MyDevice hardware."""

    # We can define fields using `field`
    some_param: str = field(default="example")

    # We must always define the client class for our driver
    # The client class can be our own client or a generic client such as `PowerClient`
    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_mydevice.client.MyDeviceClient"

    # This will "export" this method to gRPC and be callable from the client
    @export
    async def power_on(self) -> None:
        """Power on the device."""
        # No return value required
        pass

    @export
    async def power_off(self) -> str:
        """Power off the device."""
        # We can return values as well (supports most simple Python types)
        return "ok"

    @export
    async def streaming(self) -> AsyncGenerator[float, None]:
        yield 2.0
        yield 3.0
```

### 2. Client Interface (`client.py`)

Client-side proxy that communicates with the driver via gRPC:

Note that drivers can use client interfaces defined by other drivers just by including those drivers as a dependency and specifying the client class in the main driver class.

```python
from collections.abc import Generator
from jumpstarter.client import DriverClient


# All driver clients extend the DriverClient class
class MyDeviceClient(DriverClient):
    """Client interface for MyDevice driver."""

    # Generally driver clients should not be async or at least provide a sync version
    def power_on(self) -> None:
        """Power on the device."""
        # We can invoke "exported" methods using `self.call`
        self.call("power_on")

    def power_off(self) -> str:
        """Power off the device."""
        # Return the value from the remote driver call
        return self.call("power_off")

    def streaming(self) -> Generator[float, None, None]:
        """Read streaming data."""
        for v in self.streamingcall("streaming"):
            yield v
```

### 3. Package Registration (`__init__.py`)

Export the driver classes for discovery:

```python
from .client import MyDeviceClient
from .driver import MyDevice


__all__ = ["MyDevice", "MyDeviceClient"]
```

### 4. Entry Points (`pyproject.toml`)

Register the driver with Jumpstarter's plugin system:

```toml
[project.entry-points."jumpstarter.drivers"]
MyDevice = "jumpstarter_driver_mydevice.driver:MyDevice"
```

Register Jumpstarter adapters with the plugin system:

```toml
[project.entry-points."jumpstarter.adapoters"]
MyDevice = "jumpstarter_driver_mydevice.adapter:MyAdapter"
```

## Driver Patterns

### Configuration Handling

Drivers are Python dataclasses that can take configuration as keywords through the YAML configuration file.

```python
from dataclasses import field
from pydantic import BaseModel, Field
from pydantic.dataclasses import dataclass


# Config files use the `BaseModel` and `Field` from Pydantic for validation
class MyConfig(BaseModel):
    name: str = Field(default="test")


# Drivers use the `@dataclass` decorator from Pydantic and `field` from `dataclasses`
@dataclass(kw_only=True)
class MyDevice(Driver):
    # Reference config class
    config: MyConfig = field(default_factory=MyConfig)

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_mydevice.client.MyDeviceClient"

    # We can define a `__post_init__` method to do additional initialization
    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()
        self.something_else = self.config.name
```

### Async/Await Support

All exported driver methods should be async (if possible) for a consistent API:

```python
@export
async def read_sensor(self) -> float:
    """Read sensor value asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{self.base_url}/sensor") as response:
            data = await response.json()
            return data["value"]
```

All driver client methods should be sync (if possible) for compatibility with scripts.

### Driver CLI

Drivers can expose custom CLI methods through the `j` command using the `cli()` method.

Example driver CLI:

```python
import click

from jumpstarter.client import DriverClient


class MyDeviceClient(DriverClient):
    # ... other driver methods

    def cli(self):
        @click.group
        def base():
            """My Device Driver"""
            pass

        @base.command()
        @click.option("--option", default="abc")
        @click.argument("name")
        def do_something(option: str, name: str):
            # Call other driver client methods
            pass

        # Always return the constructed base
        return base
```

### Error Handling

Use appropriate exceptions for different error conditions:

```python
from jumpstarter.common.exceptions import DriverError, ConfigurationError
from jumpstarter.driver import Driver


class MyDevice(Driver):
    @export
    async def connect(self):
        try:
            # Connection logic
            pass
        except ConnectionError as e:
            raise DriverError(f"Failed to connect to device: {e}") from e
```

### Resource Management

Implement proper cleanup when a lease ends:

```python
class MyDevice(Driver):
    # The close method allows us to configure lease end actions
    def close(self):
        self.off()
```

### Driver Tree

Drivers can register children that will be exposed through a `jumpstarter_driver_composite.client.CompositeClient` or a class that inherits from it.

Make sure to add the `jumpstarter-driver-composite` dependency to the driver's `pyproject.toml`.

Custom composite client implementation:

```python
from jumpstarter_driver_composite.client import CompositeClient


# Stub custom composite client
class MyHarnessClient(CompositeClient):
    """A custom client class."""
    pass
```

Composite driver with one or more children:

```python
class MyHarness(Driver):

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_mydevice.client.MyHarnessClient"

    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()

        # Add a child power driver, passes `self` as the parent
        self.children["device"] = MyDevice(parent=self)
```

Child driver implementation:

```python
from jumpstarter.driver import Driver


class MyDevice(Driver):
    # Parent allows us to access the parent `MyDevice` driver
    parent: MyDevice
    # ... driver implementation
```

### Port Forwarding

Sometimes it is necessary to port forward from the exporter host to the client. This can be accomplished by extending the `jumpstarter_driver_network.driver.TcpNetwork` driver class and the `jumpstarter_driver_network.adapters.TcpPortForwardAdapter`.

Make sure to add the `jumpstarter-driver-network` dependency to the driver's `pyproject.toml`.

Driver implementation:

```python
from jumpstarter_driver_network.driver import TcpNetwork


class MyPortforward(TcpNetwork):

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_mydevice.client.MyPortforwardClient"
```

Client implementation:

```python
from ipaddress import IPv6Address, ip_address
from threading import Event

import click

from jumpstarter_driver_composite.client import CompositeClient
from jumpstarter_driver_network.adapters import TcpPortforwardAdapter


class MyPortforwardClient(DriverClient):
    def cli(self):
        @click.group
        def base():
            """Generic Network Connection"""
            pass

        @base.command()
        @click.option("--address", default="localhost", show_default=True)
        @click.argument("port", type=int)
        def forward_tcp(address: str, port: int):
            """
            Forward local TCP port to remote network

            PORT is the TCP port to listen on.
            """

            with TcpPortforwardAdapter(
                client=self,
                local_host=address,
                local_port=port,
            ) as addr:
                host = ip_address(addr[0])
                port = addr[1]
                match host:
                    case IPv6Address():
                        click.echo("[{}]:{}".format(host, port))
                    case _:
                        click.echo("{}:{}".format(host, port))

                Event().wait()
```

## Common Driver Types

### 1. Power Control Drivers

Base interfaces and clients are provided by the `jumpstarter-driver-power` package.

Manage device power states:

- `on()`, `off()`, `cycle()`
- Status monitoring: `read()`
- Examples: energenie, yepkit, tasmota

### 2. Communication Drivers

Handle device communication protocols:

- Serial communication: pyserial, uboot
- Network protocols: http, snmp, shell
- Custom protocols: specific device interfaces

### 3. Storage Drivers

Manage device storage and file operations:

- File transfer: tftp, opendal
- Disk imaging: sdwire
- Boot media management

### 4. Debug/Development Drivers

Support debugging and development workflows:

- Hardware debugging: probe-rs
- Virtualization: qemu
- Platform-specific: raspberrypi, corellium

## Common Driver Packages

If the driver needs to inherit from other driver packages, make sure to add the dependency to the driver's `pyproject.toml`.

- `jumpstarter-driver-composite`: Base classes for building composite drivers.
- `jumpstarter-driver-network`: Base classes and adapters for building network drivers.
- `jumpstarter-driver-power`: Base classes for building power drivers.

## Testing Patterns

### Driver Unit Tests (`driver_test.py`)

Test driver functionality in isolation:

```python
import pytest
from jumpstarter_driver_mydevice import MyDevice


@pytest.mark.asyncio
async def test_power_cycle():
    config = {"host": "test.example.com"}
    driver = MyDevice(config)

    await driver.power_on()
    assert await driver.is_powered()

    await driver.power_off()
    assert not await driver.is_powered()
```

### Driver Client Tests (`client_test.py`)

To test creating a driver and instantiating the correct client class, we can use the `jumpstarter.common.utils.serve` function.

Here is an example using `serve` to test a driver class:

```python
from jumpstarter.common.utils import serve

from .driver import ExampleDriver


def test_driver_example():
    instance = ExampleDriver(my_argument=True)

    with serve(instance) as client:
        assert client.example() == 1
```

## Configuration Examples

### Exporter Configuration (`examples/exporter.yaml`)

Show how to use the driver in practice:

```yaml
# Example configuration for MyDevice driver
export:
  my_device:
    type: jumpstarter_driver_mydevice.driver.MyDevice
    config:
      some_param: "Hello, world" # Simple config param
      config: # Nested configuration object
        name: "Some config"
```

## Development Best Practices

### 1. Documentation

- Clear docstrings for all public methods
- Type hints for better IDE support
- Configuration parameter documentation
- Usage examples in README

### 2. Error Handling

- Meaningful error messages
- Proper exception types
- Graceful failure modes
- Logging for debugging

### 3. Performance

- Async/await for I/O operations
- Connection pooling where appropriate
- Efficient resource usage
- Proper cleanup

### 4. Compatibility

- Support for different device firmware versions
- Graceful degradation for missing features
- Clear version requirements
- Cross-platform considerations

## Driver Creation Workflow

1. **Generate Skeleton**: Use `make create-driver` to create basic structure
2. **Implement Core Logic**: Add driver-specific functionality
3. **Create Client Interface**: Implement client proxy methods
4. **Add Tests**: Unit and integration tests
5. **Document Usage**: README and configuration examples
6. **Test Integration**: Verify with real hardware
7. **Submit for Review**: Follow project contribution guidelines

The driver creation command automatically:

- Creates proper package structure
- Generates boilerplate code
- Adds to workspace configuration
- Sets up documentation templates
