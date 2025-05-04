import os
import subprocess
import sys
from contextlib import contextmanager
from typing import Generator

import adbutils
import asyncclick as click
from anyio import Event
from jumpstarter_driver_network.adapters import TcpPortforwardAdapter

from jumpstarter.client import DriverClient


class AdbClient(DriverClient):
    """Power client for controlling power devices."""

    @contextmanager
    def forward_adb(self, host: str, port: int) -> Generator[str, None, None]:
        """
        Port-forward remote ADB server to local host and port.

        Args:
            host (str): The local host to forward to.
            port (int): The local port to forward to.

        Yields:
            str: The address of the forwarded ADB server.
        """
        with TcpPortforwardAdapter(
            client=self,
            local_host=host,
            local_port=port,
        ) as addr:
            yield addr

    @contextmanager
    def adb_client(self, host: str = "127.0.0.1", port: int = 5037) -> Generator[adbutils.AdbClient, None, None]:
        """
        Context manager to get an `adbutils.AdbClient`.

        Args:
            host (str): The local host to forward to.
            port (int): The local port to forward to.

        Yields:
            adbutils.AdbClient: The `adbutils.AdbClient` instance.
        """
        with self.forward_adb(host, port) as addr:
            client = adbutils.AdbClient(host=addr[0], port=int(addr[1]))
            yield client
            Event.wait()

    def cli(self):
        @click.command(context_settings={"ignore_unknown_options": True})
        @click.option("host", "-H", default="127.0.0.1", show_default=True, help="Local adb host to forward to.")
        @click.option("port", "-P", type=int, default=5037, show_default=True, help="Local adb port to forward to.")
        @click.option("-a", is_flag=True, hidden=True)
        @click.option("-d", is_flag=True, hidden=True)
        @click.option("-e", is_flag=True, hidden=True)
        @click.option("-L", hidden=True)
        @click.option("--one-device", hidden=True)
        @click.option(
            "--adb",
            default="adb",
            show_default=True,
            help="Path to the ADB executable",
            type=click.Path(exists=True, dir_okay=False, resolve_path=True),
        )
        @click.argument("args", nargs=-1)
        def adb(
            host: str,
            port: int,
            adb: str,
            a: bool,
            d: bool,
            e: bool,
            l: str,  # noqa: E741
            one_device: str,
            args: tuple[str, ...],
        ):
            """
            Run commands using a local adb executable against the remote adb server. This command is a wrapper around
            the adb command-line tool. It allows you to run adb commands against a remote ADB server tunneled through
            Jumpstarter.

            When executing this command, the adb server address and port are forwarded to the local ADB executable. The
            adb server address and port are set in the environment variables ANDROID_ADB_SERVER_ADDRESS and
            ANDROID_ADB_SERVER_PORT, respectively. This allows the local ADB executable to communicate with the remote
            adb server.

            Most command line arguments and commands are passed directly to the adb executable. However, some
            arguments and commands are not supported by the Jumpstarter adb client. These options include:
            -a, -d, -e, -L, --one-device.

            The following adb commands are also not supported: start-server, kill-server, connect, disconnect,
            reconnect, nodaemon, pair
            """
            # Throw exception for all unsupported arguments
            if any([a, d, e, l, one_device]):
                raise click.UsageError(
                    "ADB options -a, -d, -e, -L, and --one-device are not supported by the Jumpstarter ADB client"
                )
            # Check for unsupported server management commands
            unsupported_commands = [
                "start-server",
                "kill-server",
                "connect",
                "disconnect",
                "reconnect",
                "nodaemon",
                "pair",
            ]
            for arg in args:
                if arg in unsupported_commands:
                    raise click.UsageError(f"ADB command '{arg}' is not supported by the Jumpstarter ADB client")

            # Forward the ADB server address and port and call ADB executable with args
            with self.forward_adb(host, port) as addr:
                env = os.environ | {
                    "ANDROID_ADB_SERVER_ADDRESS": addr[0],
                    "ANDROID_ADB_SERVER_PORT": str(addr[1]),
                }
                cmd = [adb, *args]
                print(cmd)
                process = subprocess.Popen(cmd, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, env=env)
                return process.wait()

        return adb
