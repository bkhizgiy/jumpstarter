import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import asyncssh
from jumpstarter_driver_network.driver import NetworkInterface

from jumpstarter.driver import Driver, export, exportstream


@dataclass(kw_only=True)
class SshNetwork(NetworkInterface, Driver):
    """SSH driver for Jumpstarter providing secure shell access and tunneling.

    This driver uses AsyncSSH for pure Python SSH connections with support for:
    - Password and key-based authentication
    - SSH tunneling and port forwarding
    - Command execution and interactive shells
    - Connection management and resource cleanup

    Examples:
        Basic SSH connection:
        >>> config = {
        ...     "host": "192.168.1.100",
        ...     "username": "admin",
        ...     "password": "secret123"
        ... }
        >>> ssh = SshNetwork(**config)

        SSH with private key:
        >>> config = {
        ...     "host": "192.168.1.100",
        ...     "username": "admin",
        ...     "private_key_path": "/path/to/key.pem"
        ... }
        >>> ssh = SshNetwork(**config)
    """

    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    host_key_checking: bool = True
    connect_timeout: int = 30
    keepalive_interval: int = 30

    _connection: Optional[asyncssh.SSHClientConnection] = field(init=False, default=None)

    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()

        # Validate configuration
        if not self.password and not self.private_key_path:
            raise ValueError("Either password or private_key_path must be provided")

        if self.private_key_path and not Path(self.private_key_path).exists():
            raise FileNotFoundError(f"Private key file not found: {self.private_key_path}")

    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_ssh.client.SshNetworkClient"

    async def _get_connection(self) -> asyncssh.SSHClientConnection:
        """Get or create SSH connection."""
        if self._connection is None or self._connection.is_closed():
            self._connection = await self._create_connection()
        return self._connection

    async def _create_connection(self) -> asyncssh.SSHClientConnection:
        """Create a new SSH connection."""
        self.logger.debug("Creating SSH connection to %s:%d", self.host, self.port)

        # Prepare authentication options
        auth_options = {}

        if self.password:
            auth_options["password"] = self.password

        if self.private_key_path:
            # Load private key
            if self.private_key_passphrase:
                private_key = asyncssh.import_private_key(
                    Path(self.private_key_path).read_text(),
                    passphrase=self.private_key_passphrase
                )
            else:
                private_key = asyncssh.import_private_key(
                    Path(self.private_key_path).read_text()
                )
            auth_options["client_keys"] = [private_key]

        # Configure connection options
        connect_options = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "connect_timeout": self.connect_timeout,
            "keepalive_interval": self.keepalive_interval,
            **auth_options
        }

        # Handle host key checking
        if not self.host_key_checking:
            connect_options["known_hosts"] = None

        try:
            connection = await asyncssh.connect(**connect_options)
            self.logger.info("SSH connection established to %s:%d", self.host, self.port)
            return connection
        except Exception as e:
            self.logger.error("Failed to establish SSH connection: %s", e)
            raise

    @exportstream
    @asynccontextmanager
    async def connect(self):
        """Provide a stream interface to the SSH connection for tunneling."""
        connection = await self._get_connection()

        # Create a bidirectional stream using stdin/stdout
        stdin = connection.stdin
        stdout = connection.stdout

        # Create a wrapper that provides the stream interface
        class SshStream:
            def __init__(self, stdin, stdout):
                self.stdin = stdin
                self.stdout = stdout

            async def send(self, data: bytes):
                self.stdin.write(data)
                await self.stdin.drain()

            async def receive(self, max_bytes: int = 65536) -> bytes:
                return await self.stdout.read(max_bytes)

            def close(self):
                self.stdin.close()

        stream = SshStream(stdin, stdout)
        try:
            yield stream
        finally:
            stream.close()

    @export
    async def execute(self, command: str, timeout: Optional[int] = None) -> dict:
        """Execute a command on the remote host.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds

        Returns:
            Dictionary containing:
            - exit_code: Command exit code
            - stdout: Standard output
            - stderr: Standard error
            - success: True if exit code is 0
        """
        connection = await self._get_connection()

        try:
            self.logger.debug("Executing command: %s", command)

            # Execute command with timeout
            if timeout:
                result = await asyncio.wait_for(
                    connection.run(command, check=False),
                    timeout=timeout
                )
            else:
                result = await connection.run(command, check=False)

            response = {
                "exit_code": result.exit_status,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.exit_status == 0
            }

            self.logger.debug("Command completed with exit code: %d", result.exit_status)
            return response

        except asyncio.TimeoutError:
            self.logger.error("Command timed out after %s seconds", timeout)
            raise
        except Exception as e:
            self.logger.error("Command execution failed: %s", e)
            raise

    @export
    async def shell(self) -> AsyncGenerator[str, str]:
        """Start an interactive shell session.

        Yields:
            Shell output as strings

        Accepts:
            Commands to send to the shell
        """
        connection = await self._get_connection()

        try:
            self.logger.debug("Starting interactive shell")

            # Start interactive shell
            process = await connection.create_process()

            # Send initial prompt
            yield "Shell session started. Type 'exit' to quit.\n"

            while True:
                try:
                    # Wait for input from client
                    command = yield

                    if command.strip().lower() == 'exit':
                        break

                    # Send command to shell
                    process.stdin.write(command + '\n')
                    await process.stdin.drain()

                    # Read response (with timeout)
                    try:
                        output = await asyncio.wait_for(
                            process.stdout.read(1024),
                            timeout=5.0
                        )
                        if output:
                            yield output
                    except asyncio.TimeoutError:
                        yield "Command timed out\n"

                except Exception as e:
                    self.logger.error("Shell error: %s", e)
                    yield f"Error: {e}\n"
                    break

            # Clean up
            process.terminate()
            yield "Shell session ended.\n"

        except Exception as e:
            self.logger.error("Failed to start shell: %s", e)
            raise

    @export
    async def test_connection(self) -> dict:
        """Test SSH connection and return status information.

        Returns:
            Dictionary containing connection status and server info
        """
        try:
            connection = await self._get_connection()

            # Get server information
            server_info = {
                "connected": True,
                "host": self.host,
                "port": self.port,
                "username": self.username,
                "server_version": str(connection.get_server_version()),
                "client_version": str(connection.get_client_version()),
                "cipher": connection.get_cipher(),
                "mac": connection.get_mac(),
                "compression": connection.get_compression(),
            }

            # Test basic command execution
            try:
                result = await connection.run("echo 'connection test'", check=False)
                server_info["command_test"] = result.exit_status == 0
            except Exception as e:
                server_info["command_test"] = False
                server_info["command_error"] = str(e)

            self.logger.info("Connection test successful")
            return server_info

        except Exception as e:
            self.logger.error("Connection test failed: %s", e)
            return {
                "connected": False,
                "error": str(e),
                "host": self.host,
                "port": self.port,
                "username": self.username,
            }

    @export
    async def upload_file(self, local_path: str, remote_path: str) -> dict:
        """Upload a file to the remote host using SFTP.

        Args:
            local_path: Local file path
            remote_path: Remote file path

        Returns:
            Dictionary containing upload status
        """
        connection = await self._get_connection()

        try:
            self.logger.debug("Uploading file: %s -> %s", local_path, remote_path)

            # Use SFTP for file transfer
            async with connection.start_sftp_client() as sftp:
                await sftp.put(local_path, remote_path)

            self.logger.info("File uploaded successfully")
            return {
                "success": True,
                "local_path": local_path,
                "remote_path": remote_path,
                "message": "File uploaded successfully"
            }

        except Exception as e:
            self.logger.error("File upload failed: %s", e)
            return {
                "success": False,
                "local_path": local_path,
                "remote_path": remote_path,
                "error": str(e)
            }

    @export
    async def download_file(self, remote_path: str, local_path: str) -> dict:
        """Download a file from the remote host using SFTP.

        Args:
            remote_path: Remote file path
            local_path: Local file path

        Returns:
            Dictionary containing download status
        """
        connection = await self._get_connection()

        try:
            self.logger.debug("Downloading file: %s -> %s", remote_path, local_path)

            # Use SFTP for file transfer
            async with connection.start_sftp_client() as sftp:
                await sftp.get(remote_path, local_path)

            self.logger.info("File downloaded successfully")
            return {
                "success": True,
                "remote_path": remote_path,
                "local_path": local_path,
                "message": "File downloaded successfully"
            }

        except Exception as e:
            self.logger.error("File download failed: %s", e)
            return {
                "success": False,
                "remote_path": remote_path,
                "local_path": local_path,
                "error": str(e)
            }

    def close(self):
        """Close SSH connection when driver is closed."""
        if self._connection and not self._connection.is_closed():
            self.logger.debug("Closing SSH connection")
            self._connection.close()
            self._connection = None
