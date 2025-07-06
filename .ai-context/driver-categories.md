# Driver Categories and Classification

This document categorizes Jumpstarter drivers by functionality and provides common patterns for each category.

## Driver Categories

### Power Control Drivers

**Purpose**: Manage device power states and electrical control

**Base Package**: `jumpstarter-driver-power`

- Provides `PowerClient` base class
- Common interface: `on()`, `off()`, `cycle()`, `read()`

**Examples**:

- `jumpstarter-driver-energenie` - Energenie power switches
- `jumpstarter-driver-yepkit` - YepKit USB power controllers
- `jumpstarter-driver-tasmota` - Tasmota smart plugs
- `jumpstarter-driver-http-power` - HTTP-based power control

**Common Pattern**:

```python
from jumpstarter_driver_power.client import PowerClient


class MyPowerClient(PowerClient):
    def on(self) -> None:
        self.call("power_on")

    def off(self) -> None:
        self.call("power_off")
```

### Communication Drivers

**Purpose**: Handle device communication protocols and interfaces

**Subcategories**:

- **Serial Communication**: UART, USB-Serial, console access
- **Network Communication**: HTTP, SNMP, custom protocols
- **Shell/Command**: Remote shell execution

**Examples**:

- `jumpstarter-driver-pyserial` - Serial port communication
- `jumpstarter-driver-uboot` - U-Boot bootloader interaction
- `jumpstarter-driver-shell` - Shell command execution
- `jumpstarter-driver-http` - HTTP client functionality
- `jumpstarter-driver-snmp` - SNMP protocol support

**Common Patterns**:

```python
# Serial communication
class SerialClient(DriverClient):
    def write(self, data: bytes) -> None:
        self.call("write", data)

    def read(self, size: int) -> bytes:
        return self.call("read", size)

# Network communication
class NetworkClient(DriverClient):
    def get(self, path: str) -> dict:
        return self.call("http_get", path)
```

### Storage Drivers

**Purpose**: Manage storage devices, file systems, and data transfer

**Base Package**: `jumpstarter-driver-opendal`

- Provides storage abstraction layer
- File transfer and management

**Examples**:

- `jumpstarter-driver-tftp` - TFTP file transfer
- `jumpstarter-driver-opendal` - OpenDAL storage backends
- `jumpstarter-driver-sdwire` - SD card switching/imaging

**Common Pattern**:

```python
class StorageClient(DriverClient):
    def upload(self, local_path: str, remote_path: str) -> None:
        self.call("upload", local_path, remote_path)

    def download(self, remote_path: str, local_path: str) -> None:
        self.call("download", remote_path, local_path)
```

### Debug and Development Drivers

**Purpose**: Support debugging, firmware flashing, and development workflows

**Examples**:

- `jumpstarter-driver-probe-rs` - Hardware debugging with probe-rs
- `jumpstarter-driver-flashers` - Firmware flashing utilities
- `jumpstarter-driver-raspberrypi` - Raspberry Pi specific functions

**Common Pattern**:

```python
class DebugClient(DriverClient):
    def flash_firmware(self, firmware_path: str) -> None:
        self.call("flash_firmware", firmware_path)
    
    def reset_target(self) -> None:
        self.call("reset_target")
```

### Virtualization Drivers

**Purpose**: Control virtual machines and simulated hardware

**Examples**:

- `jumpstarter-driver-qemu` - QEMU virtual machines
- `jumpstarter-driver-corellium` - Corellium iOS simulation

**Common Pattern**:

```python
class VirtualizationClient(DriverClient):
    def start_vm(self, config: dict) -> str:
        return self.call("start_vm", config)

    def stop_vm(self, vm_id: str) -> None:
        self.call("stop_vm", vm_id)
```

### Network Infrastructure Drivers

**Purpose**: Network management and connectivity

**Base Package**: `jumpstarter-driver-network`

- Provides network abstraction
- Port forwarding and tunneling

**Examples**:

- `jumpstarter-driver-network` - Network base functionality
- Custom network drivers for specific hardware

**Common Pattern**:

```python
from jumpstarter_driver_network.client import NetworkClient

class MyNetworkClient(NetworkClient):
    def configure_interface(self, interface: str, config: dict) -> None:
        self.call("configure_interface", interface, config)
```

### Streaming and Media Drivers

**Purpose**: Handle video, audio, and streaming data

**Examples**:

- `jumpstarter-driver-ustreamer` - Video streaming
- `jumpstarter-driver-can` - CAN bus communication

**Common Pattern**:

```python
class StreamingClient(DriverClient):
    def start_stream(self, config: dict) -> str:
        return self.call("start_stream", config)
    
    def get_frame(self) -> bytes:
        return self.call("get_frame")
```

### Composite Drivers

**Purpose**: Combine multiple drivers into higher-level abstractions

**Base Package**: `jumpstarter-driver-composite`

- Provides composite driver patterns
- Child driver management

**Examples**:

- Test harness drivers combining power, serial, and network
- Platform-specific driver collections

**Common Pattern**:

```python
from jumpstarter_driver_composite.client import CompositeClient

class TestHarnessClient(CompositeClient):
    @property
    def power(self) -> PowerClient:
        return self.children["power"]
    
    @property
    def serial(self) -> SerialClient:
        return self.children["serial"]
```

## Driver Development Guidelines by Category

### Power Control

- Implement standard power interface methods
- Handle power state verification
- Support graceful shutdown sequences
- Include safety timeouts

### Communication

- Handle connection lifecycle properly
- Implement proper buffering for serial
- Support both sync and async patterns
- Handle protocol-specific error conditions

### Storage

- Implement proper file handling
- Support streaming for large files
- Handle network interruptions gracefully
- Validate file integrity

### Debug/Development

- Provide clear error messages
- Support multiple target architectures
- Handle hardware-specific quirks
- Include recovery mechanisms

### Virtualization

- Manage VM lifecycle properly
- Handle resource allocation
- Support snapshot/restore operations
- Provide console access

### Network

- Handle network configuration safely
- Support multiple protocols
- Implement proper cleanup
- Handle network topology changes

### Streaming/Media

- Handle real-time data efficiently
- Support multiple formats
- Implement proper buffering
- Handle stream interruptions

### Composite

- Manage child driver lifecycle
- Provide unified interfaces
- Handle inter-driver dependencies
- Support partial failure modes

## Configuration Patterns by Category

### Power Control Config

```yaml
power:
  type: jumpstarter_driver_energenie.driver.Energenie
  config:
    host: "192.168.1.100"
    port: 1
    timeout: 10
```

### Communication Config

```yaml
serial:
  type: jumpstarter_driver_pyserial.driver.PySerial
  config:
    url: "/dev/ttyUSB0"
    baudrate: 115200
    timeout: 5
```

### Storage Config

```yaml
storage:
  type: jumpstarter_driver_tftp.driver.TFTP
  config:
    host: "192.168.1.100"
    port: 69
    timeout: 30
```

### Composite Config

```yaml
test_harness:
  type: jumpstarter_driver_composite.driver.Composite
  config:
    children:
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

## Testing Patterns by Category

### Power Control Testing

```python
@pytest.mark.anyio
async def test_power_cycle():
    driver = PowerDriver(host="test.com", port=1)
    await driver.power_on()
    assert await driver.is_powered()
    await driver.power_off()
    assert not await driver.is_powered()
```

### Communication Testing

```python
@pytest.mark.anyio
async def test_serial_communication():
    driver = SerialDriver(url="/dev/null")
    await driver.write(b"test\n")
    response = await driver.read(100)
    assert response == b"test response"
```

### Storage Testing

```python
@pytest.mark.anyio
async def test_file_transfer():
    driver = StorageDriver(host="test.com")
    await driver.upload("local.txt", "remote.txt")
    await driver.download("remote.txt", "downloaded.txt")
    assert Path("downloaded.txt").exists()
```

This categorization helps developers understand which patterns to follow when creating new drivers and which existing drivers to reference for similar functionality.
