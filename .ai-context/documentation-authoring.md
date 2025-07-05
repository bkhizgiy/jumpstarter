# Documentation Authoring Guide

This guide covers how to write, build, and maintain documentation for Jumpstarter using the project's Sphinx-based documentation system.

## Documentation System Overview

### Technology Stack

- **Sphinx**: Primary documentation generator
- **MyST Parser**: Markdown support with enhanced syntax
- **Furo Theme**: Clean, modern documentation theme
- **Mermaid**: Diagram generation
- **sphinx-click**: Automatic CLI documentation
- **sphinx-copybutton**: Copy code blocks functionality

### Documentation Structure

```text
docs/
├── source/
│   ├── conf.py                   # Sphinx configuration
│   ├── index.rst                 # Main documentation index
│   ├── introduction/             # Getting started guides
│   │   ├── drivers.md            # Driver system overview
│   │   ├── exporters.md          # Exporter documentation
│   │   └── ...
│   ├── reference/                # API documentation
│   │   ├── package-apis/         # Auto-generated API docs
│   │   └── cli/                  # CLI reference
│   ├── tutorials/                # Step-by-step guides
│   ├── how-to/                   # Task-oriented guides
│   └── _static/                  # Static assets (images, CSS, JS)
├── Makefile                      # Build automation
├── multiversion.sh               # Multi-version build script
└── build/                        # Generated documentation
```

## Writing Documentation

### MyST Markdown Syntax

We use the MyST Markdown syntax for documentation files.

#### Basic Formatting

`````markdown
# Main Heading

## Section Heading

### Subsection Heading

**Bold text** and *italic text*

`inline code` and larger code blocks:

```{code-block} python
def example_function():
    return "Hello, World!"
```

```{code-block} console
$ console-code-block
```

````{tab} And Tabs
This is within a tab called "And Tabs"
```{code-block} console
$ code-in-tab
```
````

````{tab} Another
This is another tab called "Another"
````

- Bulleted lists
- With multiple items

1. Numbered lists
2. Are also supported

#### Cross-References

Link to other documents:

[Driver Development](../reference/drivers.md)

Link to specific sections:

[Authentication](authentication.md#jwt-tokens)

Link to API documentation:

{class}`jumpstarter.driver.Driver`
{func}`jumpstarter.client.connect`
`````

#### Code Documentation

````markdown
# Document code with syntax highlighting

```{code-block} python
from jumpstarter.driver import Driver, export

class MyDriver(Driver):
    @export
    def power_on(self) -> bool:
        """Power on the device."""
        return True
```
````

#### Include testable code examples

````markdown
```{testcode}
import jumpstarter
client = jumpstarter.connect("local")
assert client.status() == "connected"
```
````

#### Admonitions and Callouts

````markdown
```{note}
This is a note with helpful information.
```

```{warning}
This is a warning about potential issues.
```

```{important}
This highlights critical information.
```

```{tip}
This provides helpful tips and best practices.
```

```{danger}
This warns about dangerous operations.
```
````

### Diagrams with Mermaid

#### Architecture Diagrams

````markdown
```{mermaid}
graph TB
    A[Client] -->|gRPC| B[Exporter]
    B --> C[Driver]
    C --> D[Hardware]

    E[Controller] -->|Route| B
    A -->|Authenticate| E
```
````

#### Sequence Diagrams

````markdown
```{mermaid}
sequenceDiagram
    participant C as Client
    participant E as Exporter
    participant D as Driver

    C->>E: PowerOn Request
    E->>D: power_on()
    D-->>E: Success
    E-->>C: PowerResponse
```
````

#### State Diagrams

````markdown
```{mermaid}
stateDiagram-v2
    [*] --> Disconnected
    Disconnected --> Connecting: connect()
    Connecting --> Connected: success
    Connecting --> Disconnected: failure
    Connected --> Disconnected: disconnect()
```
````

### API Documentation

#### Auto-Generated Documentation

API documentation is automatically generated from Python docstrings using Sphinx autodoc.

#### Docstring Format

```python
class MyDriver(Driver):
    """Driver for controlling my custom device.

    This driver provides power control and communication interfaces
    for the MyDevice hardware platform.

    Args:
        config: Device configuration dictionary

    Attributes:
        device_id: Unique device identifier
        is_connected: Connection status

    Example:
        >>> driver = MyDriver({"host": "192.168.1.100"})
        >>> driver.power_on()
        True
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the driver with configuration.

        Args:
            config: Configuration dictionary containing:
                - host: Device IP address or hostname
                - port: Communication port (default: 8080)
                - timeout: Connection timeout in seconds

        Raises:
            ConfigurationError: If required config is missing
            ConnectionError: If unable to connect to device
        """
        pass

    @export
    def power_on(self, timeout: Optional[int] = None) -> bool:
        """Turn on device power.

        Args:
            timeout: Maximum time to wait for power on in seconds.
                If None, uses default timeout from configuration.

        Returns:
            True if power on successful, False otherwise.

        Raises:
            TimeoutError: If operation exceeds timeout
            DeviceError: If hardware reports an error

        Example:
            >>> driver.power_on(timeout=30)
            True
        """
        pass
```

#### CLI Documentation

CLI documentation is automatically generated using sphinx-click:

```python
# In your CLI module
import click

@click.command()
@click.option('--config', help='Path to configuration file')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def shell(config, verbose):
    """Start an interactive shell session with the exporter.

    This command connects to a Jumpstarter exporter and provides
    an interactive Python shell with access to all exported drivers.

    Examples:
        Connect to local exporter:

            jmp shell

        Connect with specific configuration:

            jmp shell --config my-device.yaml
    """
    pass
```

### Configuration Examples

#### YAML Configuration

````markdown
## Exporter Configuration

Example configuration for a Raspberry Pi exporter:

```{code-block} yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: raspberry-pi-test
export:
  power:
    type: jumpstarter_driver_energenie.driver.Energenie
    config:
      host: "192.168.1.100"
      port: 1

  serial:
    type: jumpstarter_driver_pyserial.driver.PySerial
    config:
      url: "/dev/ttyUSB0"
      baudrate: 115200
```

**Configuration Options:**

- `host`: IP address of the Energenie power switch
- `port`: Power outlet number (1-4)
- `url`: Serial device path
- `baudrate`: Communication speed
````

## Building Documentation

### Local Development

#### Quick Build

```bash
# Build HTML documentation
make html

# Serve documentation locally with auto-reload
make docs-serve

# Clean docs build directory
make docs-clean
```

### Multi-Version Documentation

#### Building All Versions

```bash
# Build documentation for all releases
make multiversion

# Serve multi-version documentation
make serve-multiversion
```

#### Version Configuration

Multi-version builds are configured in `multiversion.sh`:

```bash
#!/bin/bash
sphinx-multiversion source build/html \
  --pre-build 'git checkout {commit}' \
  --post-build 'git checkout main'
```

## Documentation Patterns

### Driver Documentation Template

#### Driver Overview

````markdown
# MyDevice Driver

The MyDevice driver provides power control and communication interfaces
for the MyDevice hardware platform.

## Features

- Power control (on/off/cycle)
- Serial communication
- Status monitoring
- Configuration management

## Hardware Requirements

- MyDevice hardware unit
- Network connectivity
- Power supply (12V DC)

## Installation

```bash
uv add jumpstarter-driver-mydevice
```

## Configuration

```{code-block} yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: mydevice-exporter
export:
  power:
    type: jumpstarter_driver_mydevice.driver.MyDevice
    config:
      host: "192.168.1.100"
      port: 8080
      timeout: 30
```

### Configuration Options

| Option  | Type    | Required | Description                        |
| ------- | ------- | -------- | ---------------------------------- |
| host    | string  | Yes      | Device IP address                  |
| port    | integer | No       | Communication port (default: 8080) |
| timeout | integer | No       | Connection timeout in seconds      |

## Usage Examples

### Power Control
```{code-block} python
# Connect to exporter
client = jumpstarter.connect("mydevice-exporter")

# Power on device
client.power.power_on()

# Check power status
status = client.power.get_status()
print(f"Power state: {status.power_state}")
```

### Serial Communication

```{code-block} python
# Open serial connection
with client.serial.open() as serial:
    # Send command
    serial.write(b"status\n")

    # Read response
    response = serial.read(100)
    print(response.decode())
```

## API Reference

```{eval-rst}
.. automodule:: jumpstarter_driver_mydevice.driver
   :members:
   :undoc-members:
   :show-inheritance:
```

## Troubleshooting

### Common Issues

**Connection Failed**
- Verify device IP address and network connectivity
- Check firewall settings on both client and device
- Ensure device is powered on and responsive

**Authentication Errors**
- Verify credentials in configuration
- Check device authentication settings
- Ensure time synchronization between client and device

**Performance Issues**
- Reduce timeout values for faster operations
- Enable connection pooling for multiple operations
- Monitor network latency and bandwidth
````

### Tutorial Structure

````markdown
# Getting Started with Device Testing

This tutorial walks through setting up your first device test environment.

## Prerequisites

- Python 3.11 or later
- Hardware device to test
- Network connectivity

## Step 1: Installation

Install Jumpstarter CLI:

```{code-block} console
$ pip install jumpstarter-cli
```

## Step 2: Configuration

Create exporter configuration:

```yaml
# Save as device-config.yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: my-first-device
export:
  power:
    type: jumpstarter_driver_energenie.driver.Energenie
    config:
      host: "192.168.1.100"
      port: 1
```

## Step 3: Start Exporter

```{code-block} console
$ jmp exporter --config device-config.yaml
```

## Step 4: Test Connection

```{code-block} console
$ jmp shell --exporter my-first-device
```

## Step 5: Run Tests

```{code-block} python
# In the shell
client.power.power_on()
assert client.power.get_status().power_state == "on"
client.power.power_off()
```
````

## Style Guide

### Writing Style

- **Clear and Concise**: Use simple, direct language
- **Consistent Terminology**: Use the same terms throughout
- **Active Voice**: Prefer active over passive voice
- **Present Tense**: Use present tense for descriptions

### Code Examples

- **Complete Examples**: Show full, working code
- **Commented Code**: Add explanatory comments
- **Error Handling**: Include error handling in examples
- **Real-World Usage**: Use realistic scenarios

### Visual Elements

- **Screenshots**: Use sparingly, prefer code examples
- **Diagrams**: Use Mermaid for architecture and workflow diagrams
- **Tables**: Use for structured reference information
- **Callouts**: Use admonitions to highlight important information

## Contributing to Documentation

### Documentation Workflow

1. **Create Feature Branch**: `git checkout -b docs/new-feature`
2. **Write Documentation**: Follow style guide and templates
3. **Test Locally**: Build and review documentation
4. **Commit Changes**: Use clear commit messages
5. **Create Pull Request**: Include documentation review

### Review Process

- **Technical Accuracy**: Verify all code examples work
- **Clarity**: Ensure explanations are clear and complete
- **Consistency**: Check terminology and formatting
- **Completeness**: Verify all features are documented

### Maintenance

- **Regular Updates**: Keep documentation current with code changes
- **Link Validation**: Check for broken links regularly
- **User Feedback**: Incorporate user suggestions and corrections
- **Performance**: Monitor documentation build times and optimize

## Common Issues and Solutions

### Content Issues

- **Broken Links**: Use `make docs-linkcheck` to validate links
- **Missing Images**: Ensure all images are in `_static/` directory
- **Syntax Errors**: Validate MyST syntax with `make html`
