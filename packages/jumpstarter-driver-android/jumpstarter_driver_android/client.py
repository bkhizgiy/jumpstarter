from ipaddress import IPv6Address, ip_address
from threading import Event

import asyncclick as click
from jumpstarter_driver_network.adapters import TcpPortforwardAdapter

from jumpstarter.client import DriverClient


class AdbClient(DriverClient):
    """Power client for controlling power devices."""

    def cli(self):
        @click.group
        def base():
            """ADB Client"""
            pass

        @base.command()
        @click.option("--address", default="localhost", show_default=True)
        @click.option("--port", type=int, default=5037, show_default=True)
        def start(address: str, port: int):
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

        return base
