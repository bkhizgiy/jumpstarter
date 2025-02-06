from abc import ABCMeta, abstractmethod
from collections.abc import AsyncGenerator, Generator

from .common import PowerReading
from jumpstarter.driver import Driver, export


class PowerInterface(metaclass=ABCMeta):
    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_power.client.PowerClient"

    @abstractmethod
    async def on(self): ...

    @abstractmethod
    async def off(self): ...

    @abstractmethod
    async def read(self) -> AsyncGenerator[PowerReading, None]: ...


class MockPower(PowerInterface, Driver):
    def __init__(self, children=None):
        self._power_state = None
        super().__init__()

    @export
    async def on(self):
        self._power_state = "on"

    @export
    async def off(self):
        self._power_state = "off"

    @export
    async def read(self) -> AsyncGenerator[PowerReading, None]:
        yield PowerReading(voltage=0.0, current=0.0)
        yield PowerReading(voltage=5.0, current=2.0)


class SyncMockPower(PowerInterface, Driver):
    def __init__(self, children=None):
        self._power_state = None
        super().__init__()

    @export
    def on(self):
        self._power_state = "on"

    @export
    def off(self):
        self._power_state = "off"

    @export
    def read(self) -> Generator[PowerReading, None]:
        yield PowerReading(voltage=0.0, current=0.0)
        yield PowerReading(voltage=5.0, current=2.0)
