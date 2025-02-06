from dataclasses import dataclass

import asyncclick as click
from jumpstarter_driver_power.client import PowerClient


@dataclass(kw_only=True)
class SNMPServerClient(PowerClient):
    """Client interface for SNMP Power Control"""

    def on(self) -> str:
        """Turn power on"""
        return self.call("on")

    def off(self) -> str:
        """Turn power off"""
        return self.call("off")

    def cli(self):
        @click.group()
        def snmp():
            """SNMP power control commands"""
            pass

        for cmd in super().cli().commands.values():
            snmp.add_command(cmd)

        @snmp.command()
        def cycle():
            """Power cycle the device"""
            result = self.cycle()
            click.echo(result)

        return snmp
