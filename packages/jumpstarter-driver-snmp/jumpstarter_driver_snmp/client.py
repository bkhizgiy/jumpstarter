from dataclasses import dataclass

import asyncclick as click

from jumpstarter.client import DriverClient


@dataclass(kw_only=True)
class SNMPServerClient(DriverClient):
    """Client interface for SNMP Power Control"""

    def power_on(self):
        """Turn power on"""
        return self.call("power_on")

    def power_off(self):
        """Turn power off"""
        return self.call("power_off")

    def power_cycle(self):
        """Power cycle the device"""
        return self.call("power_cycle")

    def cli(self):
        @click.group()
        def snmp():
            """SNMP power control commands"""
            pass

        @snmp.command()
        def on():
            """Turn power on"""
            result = self.power_on()
            click.echo(result)

        @snmp.command()
        def off():
            """Turn power off"""
            result = self.power_off()
            click.echo(result)

        @snmp.command()
        def cycle():
            """Power cycle the device"""
            result = self.power_cycle()
            click.echo(result)

        return snmp
