# CLI Tools and Commands

Jumpstarter provides two main CLI tools for interacting with devices and managing the framework. This document covers the command structure, common usage patterns, and key functionality.

## Primary CLI Tools

### `jmp` - Main Jumpstarter CLI

The primary command-line interface for Jumpstarter operations.

**Installation**: Included with `jumpstarter-cli` package
**Location**: `packages/jumpstarter-cli/jumpstarter_cli/jmp.py`

### `j` - Jumpstarter Shell CLI

The `j` CLI only works within a `jmp shell` session and provides dynamic access to all the registered driver client CLIs.

**Installation**: Included with `jumpstarter-cli` package
**Location**: `packages/jumpstarter-cli/jumpstarter_cli/j.py`
**Availability**: Only available within a `jmp shell` session
**Use Case**: Used to interact with driver clients that provide CLIs

## Command Categories

### Configuration Management

#### `jmp config`

Manage client and exporter configurations:

```bash
# Client configuration
jmp config client create my-client --endpoint https://jumpstarter.example.com
jmp config client use my-client
jmp config client list

# Exporter configuration
jmp config exporter create my-device --config device.yaml
jmp config exporter use my-device
jmp config exporter list
```

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/config.py`

#### Configuration File Hierarchy

Jumpstarter loads configuration in the following order (highest to lowest priority):

1. **Command-line options** (highest priority)
2. **Environment variables**
3. **Configuration files**:
   - User configs: `~/.config/jumpstarter/clients/*.yaml`
   - System configs: `/etc/jumpstarter/exporters/*.yaml`
4. **Default values** (lowest priority)

**Client Configuration Location**: `~/.config/jumpstarter/clients/`
**Exporter Configuration Location**: `/etc/jumpstarter/exporters/`

### Device Interaction

#### `jmp shell`

Interactive shell access to devices using the `j` command:

```bash
# Create a local exporter instance by name (/etc/jumpstarter/exporters/my-device.yaml)
jmp shell --exporter my-device

# Connect a local exporter instance by config file
jmp shell --exporter-config path/to/my-exporter.yaml

# Use a selector to create a lease in distributed mode
jmp shell -l type=rpi,env=dev

# Connect to an existing lease ID
jmp shell --lease <lease-id>
```

**Features**:

- Interactive Python REPL with device access (through the `j` CLI)
- Real-time device interaction
- Session history and logging (using the service)

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/shell.py`

#### `jmp run`

Start a local exporter using a specific config.

```bash
# Run an exporter by name (/etc/jumpstarter/exporters/my-device.yaml)
jmp run --exporter my-device

# Run with a config file
jmp run --exporter-config path/to/my-exporter.yaml
```

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/run.py`

### Resource Management (Distributed Mode)

#### `jmp create`

Create resources in the Jumpstarter service:

```bash
# Create a lease for device access
jmp create lease --selector vendor=acme,model=widget --duration 1h
```

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/create.py`

#### `jmp get`

Retrieve information about resources through the Jumpstarter Service:

```bash
# List available exporters
jmp get exporters

# Show lease information
jmp get leases
```

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/get.py`

#### `jmp delete`

Remove resources through the Jumpstarter Service:

```bash
# Delete a lease
jmp delete lease <lease-id>
```

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/delete.py`

### Authentication

#### `jmp login`

Authenticate with the Jumpstarter Service:

```bash
Usage: jmp login [OPTIONS]

  Login into a jumpstarter instance

Options:
  -e, --endpoint TEXT     Enter the Jumpstarter service endpoint.
  --namespace TEXT        Enter the Jumpstarter exporter namespace.
  --name TEXT             Enter the Jumpstarter exporter name.
  --issuer TEXT           OIDC issuer
  --client-id TEXT        OIDC client id
  --token TEXT            OIDC access token
  --username TEXT         OIDC username
  --password TEXT         OIDC password
  --connector-id TEXT     OIDC token exchange connector id (Dex specific)
  --allow TEXT            A comma-separated list of driver client packages to
                          load.
  --unsafe                Should all driver client packages be allowed to load
                          (UNSAFE!).
  --insecure-tls-config   Disable endpoint TLS verification. This is insecure
                          and should only be used for testing purposes
  --nointeractive         Disable interactive prompts (for use in scripts).
  --exporter-config PATH  Path of exporter config
  --exporter TEXT         Alias of exporter config
  --client-config PATH    Path to client config
  --client TEXT           Alias of client config
  --help                  Show this message and exit.
```

**Features**:

- OAuth2/OpenID Connect integration
- JWT token management
- Multiple authentication providers
- Token refresh handling

**Implementation**: `packages/jumpstarter-cli/jumpstarter_cli/login.py`

## CLI Architecture

### Command Structure

Commands follow a hierarchical structure:

```bash
jmp [global-options] <command> [command-options] [arguments]
```

### Common Usage Patterns

#### Local Development Workflow

```bash
# Set up exporter configuration
jmp config exporter create lab-device

# Interactive development
jmp shell --exporter lab-device

# Run automated tests
jmp shell --exporter lab-device python3 ./test_suite.py
```

#### Distributed Testing Workflow

```bash
# Configure client for remote service
jmp config client create ci-client

# Authenticate
jmp login --provider corporate-sso

# Request hardware access and run tests with acquired hardware
jmp shell -l board=rpi4,location=lab1 python3 ./integration_tests.py

# Clean up
jmp delete lease <lease-id>
```

## Admin CLI Tools

### `jumpstarter-cli-admin` (`jmp admin`)

Administrative commands for service management.

**Location**: `packages/jumpstarter-cli-admin/`

#### Installation Management

```bash
# Install Jumpstarter service in a Kubernetes cluster
jmp admin install
```

#### Resource Management

```bash
# Import exporter configurations
jmp admin import exporter my-exporter
```

## Output Formats

All CLI tools support multiple output formats:

### Table Format (Default)

```bash
jmp get exporters
# Human-readable table output
```

### JSON Format

```bash
jmp get exporters --format json
# Machine-readable JSON
```

### YAML Format

```bash
jmp get exporters --format yaml
# Human and machine readable YAML
```

## Environment Variables

### Common Variables

- `JUMPSTARTER_GRPC_INSECURE` - Set to `1` to disable TLS verification globally
- `JMP_CLIENT_CONFIG` - Path to a client configuration file
- `JMP_CLIENT` - Name of a registered client config
- `JMP_NAMESPACE` - Namespace in the controller
- `JMP_NAME` - Client name
- `JMP_ENDPOINT` - gRPC endpoint (overrides config file)
- `JMP_TOKEN` - Auth token (overrides config file)
- `JMP_DRIVERS_ALLOW` - Comma-separated list of allowed driver namespaces
- `JUMPSTARTER_FORCE_SYSTEM_CERTS` - Set to `1` to force system CA certificates

## Connection URL Schemes

Jumpstarter supports multiple URL schemes for connecting to different types of endpoints:

### Local Connections

- **`local`** - Connect to local exporter by name (looks up in `/etc/jumpstarter/exporters/`)
- **`unix:///path/to/socket`** - Connect via Unix domain socket
- **Path to config file** - Direct path to exporter YAML configuration

### Remote Exporter Connections

- **`exporter://hostname:port`** - Connect to remote exporter (insecure)
- **`exporters://hostname:port`** - Connect to remote exporter with TLS encryption

### Service Connections (Distributed Mode)

- **`service://hostname`** - Connect through Jumpstarter service/controller
- **`https://hostname`** - HTTPS connection to Jumpstarter service

### Examples

```bash
# Local connections
jmp shell --exporter my-device                    # By name
jmp shell --exporter-config ./device.yaml        # By config file
jmp shell --exporter unix:///tmp/jumpstarter.sock # Unix socket

# Remote exporter
jmp shell --exporter exporter://device.lab.com:5000      # Insecure
jmp shell --exporter exporters://device.lab.com:5000     # TLS

# Service connections
jmp shell --endpoint service://jumpstarter.company.com   # Service
jmp shell -l type=rpi,env=lab                           # Lease selector
```
