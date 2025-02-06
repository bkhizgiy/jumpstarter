import pytest

from .common import PowerReading
from .driver import MockPower, SyncMockPower

pytestmark = pytest.mark.anyio


async def test_driver_mock_power():
    driver = MockPower()

    await driver.on()
    assert driver._power_state == "on"

    await driver.off()
    assert driver._power_state == "off"

    assert [v async for v in driver.read()] == [
        PowerReading(voltage=0.0, current=0.0),
        PowerReading(voltage=5.0, current=2.0),
    ]


def test_driver_sync_mock_power():
    driver = SyncMockPower()

    driver.on()
    assert driver._power_state == "on"

    driver.off()
    assert driver._power_state == "off"

    assert list(driver.read()) == [
        PowerReading(voltage=0.0, current=0.0),
        PowerReading(voltage=5.0, current=2.0),
    ]
