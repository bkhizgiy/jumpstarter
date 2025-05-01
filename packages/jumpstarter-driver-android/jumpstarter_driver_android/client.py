from jumpstarter.client import DriverClient


class AdbClient(DriverClient):
    """Power client for controlling power devices."""

    def connect(self) -> None:
        """Connect to the ADB server."""
        pass
