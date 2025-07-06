# SSH Driver for Jumpstarter

The `jumpstarter-driver-ssh` package provides a pure Python SSH driver for Jumpstarter that enables secure shell access, command execution, file transfer, and SSH tunneling capabilities without requiring external SSH client dependencies.

## Features

- **Pure Python Implementation**: Uses AsyncSSH library for native async/await support
- **Multiple Authentication Methods**: Support for password and private key authentication
- **Command Execution**: Execute remote commands with timeout support
- **Interactive Shell**: Full interactive SSH shell sessions
- **File Transfer**: Upload and download files using SFTP
- **SSH Tunneling**: Port forwarding through SSH connections
- **Connection Management**: Automatic connection pooling and cleanup
- **Comprehensive CLI**: Rich command-line interface for SSH operations

## Installation

```shell
pip3 install --extra-index-url https://pkg.jumpstarter.dev/simple/ jumpstarter-driver-ssh
```

## Quick Start

### Basic Configuration

Create an exporter configuration file:

```yaml
apiVersion: jumpstarter.dev/v1alpha1
kind: ExporterConfig
metadata:
  name: ssh-device
export:
  ssh:
    type: jumpstarter_driver_ssh.driver.SshNetwork
    config:
      host: "192.168.1.100"
      username: "admin"
      password: "secure123"
```

### Using the Driver

Start an interactive SSH session:

```bash
jmp shell --exporter ssh-device
```

In the shell, access SSH functionality:

```python
# Test the connection
j ssh test

# Execute a command
j ssh exec "ls -la /home"

# Start interactive shell
j ssh shell

# Upload a file
j ssh upload ./local-file.txt /remote/path/file.txt

# Download a file  
j ssh download /remote/file.txt ./local-file.txt

# Set up SSH tunnel
j ssh forward-tcp 8080
```

## Configuration Options

### Authentication Methods

#### Password Authentication

```yaml
export:
  ssh:
    type: jumpstarter_driver_ssh.driver.SshNetwork
    config:
      host: "device.example.com"
      username: "admin"
      password: "secure_password"
```

#### Private Key Authentication

```yaml
export:
  ssh:
    type: jumpstarter_driver_ssh.driver.SshNetwork
    config:
      host: "device.example.com"
      username: "admin"
      private_key_path: "/path/to/private/key.pem"
      private_key_passphrase: "key_passphrase"  # Optional
```

### Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | Yes | - | SSH server hostname or IP address |
| `port` | integer | No | 22 | SSH server port |
| `username` | string | Yes | - | SSH username |
| `password` | string | No | - | SSH password (required if no private key) |
| `private_key_path` | string | No | - | Path to private key file (required if no password) |
| `private_key_passphrase` | string | No | - | Passphrase for encrypted private key |
| `host_key_checking` | boolean | No | true | Enable SSH host key verification |
| `connect_timeout` | integer | No | 30 | Connection timeout in seconds |
| `keepalive_interval` | integer | No | 30 | SSH keepalive interval in seconds |

## Programming Interface

### Driver Methods

The SSH driver provides several exported methods for remote operations:

#### Command Execution

```python
# Execute a simple command
result = await ssh.execute("uptime")
print(f"Exit code: {result['exit_code']}")
print(f"Output: {result['stdout']}")

# Execute with timeout
result = await ssh.execute("long_running_command", timeout=60)
```

#### Connection Testing

```python
# Test SSH connection and get server info
status = await ssh.test_connection()
if status['connected']:
    print(f"Connected to {status['server_version']}")
else:
    print(f"Connection failed: {status['error']}")
```

#### File Transfer

```python
# Upload a file
result = await ssh.upload_file("/local/script.sh", "/tmp/script.sh")
if result['success']:
    print("File uploaded successfully")

# Download a file
result = await ssh.download_file("/var/log/system.log", "./system.log")
```

#### Interactive Shell

```python
# Start interactive shell session
async for output in ssh.shell():
    if isinstance(output, str):
        print(output, end='')
    else:
        command = input("$ ")
        output = output.send(command)
```

### Client Interface

The client provides synchronous methods for easier scripting:

```python
import jumpstarter

# Connect to SSH exporter
client = jumpstarter.connect("ssh-device")

# Execute commands
result = client.ssh.execute("hostname")
print(result['stdout'])

# Test connection
status = client.ssh.test_connection()

# File operations
client.ssh.upload_file("./config.txt", "/etc/myapp/config.txt")
client.ssh.download_file("/var/log/app.log", "./app.log")

# Run a script
result = client.ssh.run_script("./deploy.sh")

# Interactive shell context manager
with client.ssh.interactive_shell() as shell:
    output = shell.send_command("pwd")
    print(output)
```

## CLI Reference

### Available Commands

The SSH driver provides a rich CLI through the `j ssh` command:

#### `j ssh test`
Test SSH connection and display server information.

```bash
j ssh test
# Output:
# ✓ SSH connection successful
# Server: 192.168.1.100:22
# Username: admin
# Server version: OpenSSH_8.9p1
# Cipher: aes256-gcm@openssh.com
# ✓ Command execution test passed
```

#### `j ssh exec <command>`
Execute a command on the remote host.

```bash
j ssh exec "ps aux | grep nginx"
j ssh exec --timeout 60 "apt update && apt upgrade -y"
```

#### `j ssh shell`
Start an interactive SSH shell session.

```bash
j ssh shell
# Starting interactive SSH shell...
# ssh> ls -la
# ssh> cd /var/log
# ssh> exit
```

#### `j ssh upload <local_path> <remote_path>`
Upload a file to the remote host.

```bash
j ssh upload ./config.json /etc/app/config.json
j ssh upload ./deploy.sh /tmp/deploy.sh
```

#### `j ssh download <remote_path> <local_path>`
Download a file from the remote host.

```bash
j ssh download /var/log/system.log ./system.log
j ssh download /etc/hostname ./device-hostname.txt
```

#### `j ssh run-script <script_path>`
Upload and execute a script on the remote host.

```bash
j ssh run-script ./deploy.sh
j ssh run-script ./health-check.py
```

#### `j ssh forward-tcp [--address ADDRESS] <PORT>`
Forward a local TCP port through the SSH connection.

```bash
j ssh forward-tcp 8080
j ssh forward-tcp --address 0.0.0.0 3000
```

#### `j ssh forward-unix [PATH]`
Forward a local Unix domain socket through the SSH connection.

```bash
j ssh forward-unix
j ssh forward-unix /tmp/my-socket
```

## Use Cases

### 1. Device Testing and Automation

```python
# Test script automation
client = jumpstarter.connect("test-device")

# Upload test scripts
client.ssh.upload_file("./test-suite.sh", "/tmp/test-suite.sh")

# Execute tests
result = client.ssh.execute("chmod +x /tmp/test-suite.sh && /tmp/test-suite.sh")

# Download test results
client.ssh.download_file("/tmp/test-results.xml", "./results.xml")
```

### 2. Remote Configuration Management

```python
# Deploy configuration files
client.ssh.upload_file("./app-config.yaml", "/etc/myapp/config.yaml")

# Restart services
restart_result = client.ssh.execute("systemctl restart myapp")

# Verify service status
status_result = client.ssh.execute("systemctl status myapp")
```

### 3. Log Collection and Monitoring

```python
# Collect system logs
client.ssh.download_file("/var/log/syslog", "./device-syslog.txt")

# Monitor real-time logs
with client.ssh.interactive_shell() as shell:
    shell.send_command("tail -f /var/log/application.log")
```

### 4. SSH Tunneling for Service Access

```bash
# Access a web service running on the device
j ssh forward-tcp 8080

# In another terminal, access the service
curl http://localhost:8080/api/status
```

### 5. Bulk Script Execution

```python
# Deploy and run multiple scripts
scripts = ["setup.sh", "configure.sh", "start-services.sh"]

for script in scripts:
    result = client.ssh.run_script(f"./scripts/{script}")
    if not result['success']:
        print(f"Script {script} failed: {result['stderr']}")
        break
```

## Security Considerations

### Authentication Best Practices

1. **Use Private Keys**: Prefer SSH key authentication over passwords
2. **Protect Private Keys**: Store private keys securely with appropriate file permissions
3. **Key Passphrases**: Use passphrases for additional private key protection
4. **Rotate Credentials**: Regularly rotate SSH keys and passwords

### Network Security

1. **Host Key Verification**: Enable `host_key_checking` in production environments
2. **Secure Networks**: Use SSH over trusted networks or VPN connections
3. **Port Configuration**: Change default SSH port (22) if required
4. **Firewall Rules**: Restrict SSH access to required source IPs

### Configuration Security

```yaml
# Secure configuration example
export:
  ssh:
    type: jumpstarter_driver_ssh.driver.SshNetwork
    config:
      host: "device.internal.company.com"
      port: 2222  # Non-standard port
      username: "jumpstarter"
      private_key_path: "/secure/keys/jumpstarter.pem"
      private_key_passphrase: "${SSH_KEY_PASSPHRASE}"  # From environment
      host_key_checking: true  # Verify host identity
      connect_timeout: 10
      keepalive_interval: 60
```

## Troubleshooting

### Common Issues

#### Connection Failures

**Problem**: `Failed to establish SSH connection`

**Solutions**:
1. Verify host and port are correct
2. Check network connectivity: `ping <host>`
3. Verify SSH service is running: `systemctl status ssh`
4. Check firewall rules on both client and server

#### Authentication Errors

**Problem**: `Authentication failed`

**Solutions**:
1. Verify username and password/key are correct
2. Check private key file permissions (should be 600)
3. Ensure private key format is correct (OpenSSH or PEM)
4. Verify user account exists and has SSH access

#### Host Key Verification Failed

**Problem**: `Host key verification failed`

**Solutions**:
1. Remove old host key: `ssh-keygen -R <hostname>`
2. Disable host key checking (insecure): `host_key_checking: false`
3. Add correct host key to known_hosts file

#### File Transfer Errors

**Problem**: `SFTP operation failed`

**Solutions**:
1. Check file paths exist and are accessible
2. Verify user has read/write permissions
3. Ensure sufficient disk space on target
4. Check SFTP subsystem is enabled on server

### Debug Information

Enable debug logging to troubleshoot connection issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Driver will now output detailed connection information
```

## API Reference

### SshNetwork Class

```python
class SshNetwork(NetworkInterface, Driver):
    """SSH driver for secure shell connections."""
    
    # Configuration
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    host_key_checking: bool = True
    connect_timeout: int = 30
    keepalive_interval: int = 30
```

### Exported Methods

#### `execute(command: str, timeout: Optional[int] = None) -> dict`
Execute a command on the remote host.

**Returns**: Dictionary with `exit_code`, `stdout`, `stderr`, and `success` fields.

#### `test_connection() -> dict`
Test SSH connection and return server information.

**Returns**: Dictionary with connection status and server details.

#### `upload_file(local_path: str, remote_path: str) -> dict`
Upload a file using SFTP.

**Returns**: Dictionary with upload status and file paths.

#### `download_file(remote_path: str, local_path: str) -> dict`
Download a file using SFTP.

**Returns**: Dictionary with download status and file paths.

#### `shell() -> AsyncGenerator[str, str]`
Start an interactive shell session.

**Yields**: Shell output strings and accepts command input.

### Client Methods

#### SshNetworkClient Class

```python
class SshNetworkClient(NetworkClient):
    """Client interface for SSH driver."""
    
    def execute(command: str, timeout: Optional[int] = None) -> dict
    def test_connection() -> dict
    def upload_file(local_path: str, remote_path: str) -> dict
    def download_file(remote_path: str, local_path: str) -> dict
    def run_script(script_path: str) -> dict
    def interactive_shell() -> ContextManager[InteractiveShell]
```

## License

This driver is licensed under the Apache 2.0 License. See the [LICENSE](https://github.com/jumpstarter-dev/jumpstarter/blob/main/LICENSE) file for details.