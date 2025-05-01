import os
import shutil
import subprocess
from dataclasses import field
from typing import Optional, override

from jumpstarter_driver_network.driver import TcpNetwork
from pydantic.dataclasses import dataclass

from jumpstarter.common.exceptions import ConfigurationError


@dataclass(kw_only=True)
class AdbServer(TcpNetwork):
    host: str = "127.0.0.1"
    port: int = 5037
    adb_executable: Optional[str] = None

    _adb_path: Optional[str] = field(init=False, default=None)

    @classmethod
    @override
    def client(cls) -> str:
        return "jumpstarter_driver_android.client.AdbClient"

    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()

        if self.port < 0 or self.port > 65535:
            raise ConfigurationError(f"Invalid port number: {self.port}")
        if not isinstance(self.port, int):
            raise ConfigurationError(f"Port must be an integer: {self.port}")

        self.logger.info(f"ADB server will run on port {self.port}")

        if not self.adb_executable:
            self._adb_path = shutil.which("adb")
            if not self._adb_path:
                raise ConfigurationError(f"ADB executable '{self.adb_executable}' not found in PATH.")
        else:
            self._adb_path = self.adb_executable
        self.logger.info(f"ADB Executable: {self._adb_path}")

        try:
            result = subprocess.run(
                [self._adb_path, "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            self.logger.info(f"ADB Version Info: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to execute adb: {e}")

        try:
            result = subprocess.run(
                [self._adb_path, "start-server"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={"ANDROID_ADB_SERVER_PORT": str(self.port), **dict(os.environ)},
            )
            self.logger.info(f"ADB server started on port {self.port}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to start ADB server: {e}")

    def close(self):
        try:
            subprocess.run(
                [self._adb_path, "kill-server"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.logger.info("ADB server stopped")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to stop ADB server: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error while stopping ADB server: {e}")
        super().close()
