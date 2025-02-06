import time
from collections.abc import Generator

import asyncclick as click

from .common import PowerReading
from jumpstarter.client import DriverClient


class PowerClient(DriverClient):
    def on(self) -> str:
        return self.call("on")

    def off(self) -> str:
        return self.call("off")

    def cycle(self, quiescent_period: int = 2) -> str:
        """Power cycle the device"""
        self.logger.info("Starting power cycle sequence")
        self.off()
        self.logger.info(f"Waiting {quiescent_period} seconds...")
        time.sleep(quiescent_period)
        self.on()
        self.logger.info("Power cycle sequence complete")
        return "Power cycled"

    def read(self) -> Generator[PowerReading, None, None]:
        for v in self.streamingcall("read"):
            yield PowerReading.model_validate(v, strict=True)

    def cli(self):
        @click.group
        def base():
            """Generic power"""
            pass

        @base.command()
        def on():
            """Power on"""
            click.echo(self.on())

        @base.command()
        def off():
            """Power off"""
            click.echo(self.off())

        @base.command()
        @click.option('--wait', '-w', default=2, help='Wait time in seconds between off and on')
        def cycle(wait):
            """Power cycle"""
            click.echo(self.cycle(wait))

        return base
