from contextlib import contextmanager
from ipaddress import IPv6Address, ip_address
from threading import Event
from typing import Optional

import click
from jumpstarter_driver_network.adapters import TcpPortforwardAdapter, UnixPortforwardAdapter
from jumpstarter_driver_network.client import NetworkClient


class SshNetworkClient(NetworkClient):
    """
    SSH client interface for Jumpstarter SSH driver.

    This client provides methods for:
    - SSH command execution
    - Interactive shell access
    - File transfer (upload/download)
    - Connection testing
    - SSH tunneling and port forwarding
    """

    def execute(self, command: str, timeout: Optional[int] = None) -> dict:
        """Execute a command on the remote SSH host.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (optional)

        Returns:
            Dictionary containing command results and status
        """
        return self.call("execute", command=command, timeout=timeout)

    def test_connection(self) -> dict:
        """Test SSH connection and get server information.

        Returns:
            Dictionary containing connection status and server details
        """
        return self.call("test_connection")

    def upload_file(self, local_path: str, remote_path: str) -> dict:
        """Upload a file to the remote host using SFTP.

        Args:
            local_path: Path to local file
            remote_path: Target path on remote host

        Returns:
            Dictionary containing upload status
        """
        return self.call("upload_file", local_path=local_path, remote_path=remote_path)

    def download_file(self, remote_path: str, local_path: str) -> dict:
        """Download a file from the remote host using SFTP.

        Args:
            remote_path: Path to remote file
            local_path: Target path on local host

        Returns:
            Dictionary containing download status
        """
        return self.call("download_file", remote_path=remote_path, local_path=local_path)

    def run_script(self, script_path: str) -> dict:
        """Upload and execute a script on the remote host.

        Args:
            script_path: Path to local script file

        Returns:
            Dictionary containing script execution results
        """
        # Upload the script first
        remote_script_path = f"/tmp/jumpstarter_script_{id(self)}.sh"
        upload_result = self.upload_file(script_path, remote_script_path)

        if not upload_result["success"]:
            return upload_result

        # Make script executable and run it
        chmod_result = self.execute(f"chmod +x {remote_script_path}")
        if not chmod_result["success"]:
            return chmod_result

        # Execute the script
        exec_result = self.execute(remote_script_path)

        # Clean up the script file
        self.execute(f"rm -f {remote_script_path}")

        return exec_result

    @contextmanager
    def interactive_shell(self):
        """Context manager for interactive shell sessions.

        Provides a simple interface for interactive SSH sessions.

        Example:
            with client.interactive_shell() as shell:
                output = shell.send_command("ls -la")
                print(output)
        """

        class InteractiveShell:
            def __init__(self, client):
                self.client = client
                self.shell_gen = None

            def __enter__(self):
                self.shell_gen = self.client.streamingcall("shell")
                # Get initial prompt
                next(self.shell_gen)
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.shell_gen:
                    try:
                        self.shell_gen.send("exit")
                    except StopIteration:
                        pass

            def send_command(self, command: str) -> str:
                """Send a command to the shell and return the output."""
                if not self.shell_gen:
                    raise RuntimeError("Shell not initialized")

                try:
                    return self.shell_gen.send(command)
                except StopIteration:
                    raise RuntimeError("Shell session ended")

        yield InteractiveShell(self)

    def cli(self):
        """Provide CLI commands for SSH operations."""

        @click.group
        def base():
            """SSH Connection Manager"""
            pass

        @base.command()
        @click.argument("command")
        @click.option("--timeout", type=int, help="Command timeout in seconds")
        def exec(command: str, timeout: Optional[int]):
            """Execute a command on the remote SSH host"""
            result = self.execute(command, timeout=timeout)

            if result["success"]:
                click.echo(result["stdout"], nl=False)
                if result["stderr"]:
                    click.echo(result["stderr"], nl=False, err=True)
            else:
                click.echo(f"Command failed with exit code {result['exit_code']}", err=True)
                if result["stderr"]:
                    click.echo(result["stderr"], nl=False, err=True)
                if result["stdout"]:
                    click.echo(result["stdout"], nl=False)

        @base.command()
        def test():
            """Test SSH connection and display server information"""
            result = self.test_connection()

            if result["connected"]:
                click.echo("✓ SSH connection successful")
                click.echo(f"Server: {result['host']}:{result['port']}")
                click.echo(f"Username: {result['username']}")
                click.echo(f"Server version: {result['server_version']}")
                click.echo(f"Client version: {result['client_version']}")
                click.echo(f"Cipher: {result['cipher']}")
                click.echo(f"MAC: {result['mac']}")
                click.echo(f"Compression: {result['compression']}")

                if result.get("command_test", False):
                    click.echo("✓ Command execution test passed")
                else:
                    click.echo("✗ Command execution test failed")
                    if "command_error" in result:
                        click.echo(f"  Error: {result['command_error']}")
            else:
                click.echo("✗ SSH connection failed", err=True)
                click.echo(f"Error: {result['error']}", err=True)

        @base.command()
        @click.argument("local_path", type=click.Path(exists=True))
        @click.argument("remote_path")
        def upload(local_path: str, remote_path: str):
            """Upload a file to the remote host"""
            result = self.upload_file(local_path, remote_path)

            if result["success"]:
                click.echo(f"✓ File uploaded: {local_path} -> {remote_path}")
            else:
                click.echo(f"✗ Upload failed: {result['error']}", err=True)

        @base.command()
        @click.argument("remote_path")
        @click.argument("local_path", type=click.Path())
        def download(remote_path: str, local_path: str):
            """Download a file from the remote host"""
            result = self.download_file(remote_path, local_path)

            if result["success"]:
                click.echo(f"✓ File downloaded: {remote_path} -> {local_path}")
            else:
                click.echo(f"✗ Download failed: {result['error']}", err=True)

        @base.command()
        @click.argument("script_path", type=click.Path(exists=True))
        def run_script(script_path: str):
            """Upload and execute a script on the remote host"""
            result = self.run_script(script_path)

            if result["success"]:
                click.echo("✓ Script executed successfully")
                click.echo(result["stdout"], nl=False)
                if result["stderr"]:
                    click.echo(result["stderr"], nl=False, err=True)
            else:
                click.echo(f"✗ Script execution failed with exit code {result['exit_code']}", err=True)
                if result["stderr"]:
                    click.echo(result["stderr"], nl=False, err=True)
                if result["stdout"]:
                    click.echo(result["stdout"], nl=False)

        @base.command()
        def shell():
            """Start an interactive SSH shell session"""
            click.echo("Starting interactive SSH shell...")
            click.echo("Type commands and press Enter. Type 'exit' to quit.")
            click.echo("=" * 50)

            try:
                with self.interactive_shell() as shell:
                    while True:
                        try:
                            command = click.prompt("ssh", prompt_suffix="> ")
                            if command.strip().lower() == "exit":
                                break

                            output = shell.send_command(command)
                            if output:
                                click.echo(output, nl=False)
                        except KeyboardInterrupt:
                            click.echo("\nUse 'exit' to quit the shell.")
                        except EOFError:
                            break
                        except Exception as e:
                            click.echo(f"Error: {e}", err=True)
                            break
            except Exception as e:
                click.echo(f"Failed to start shell: {e}", err=True)

        @base.command()
        @click.option("--address", default="localhost", show_default=True)
        @click.argument("port", type=int)
        def forward_tcp(address: str, port: int):
            """
            Forward local TCP port to remote SSH host

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
                        click.echo(f"SSH tunnel active: [{host}]:{port}")
                    case _:
                        click.echo(f"SSH tunnel active: {host}:{port}")

                click.echo("Press Ctrl+C to stop the tunnel")
                try:
                    Event().wait()
                except KeyboardInterrupt:
                    click.echo("\nTunnel stopped")

        @base.command()
        @click.argument("path", type=click.Path(), required=False)
        def forward_unix(path: str | None):
            """
            Forward local Unix domain socket to remote SSH host

            PATH is the path of the Unix domain socket to listen on,
            defaults to a random path under $XDG_RUNTIME_DIR.
            """
            with UnixPortforwardAdapter(
                client=self,
                path=path,
            ) as addr:
                click.echo(f"SSH tunnel active: {addr}")
                click.echo("Press Ctrl+C to stop the tunnel")
                try:
                    Event().wait()
                except KeyboardInterrupt:
                    click.echo("\nTunnel stopped")

        return base
