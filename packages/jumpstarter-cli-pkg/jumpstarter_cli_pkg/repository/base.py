from abc import ABC, abstractmethod

from .package import (
    V1Alpha1DriverPackageList,
)


class DriverRepository(ABC):
    """
    A repository of driver packages.
    """

    @abstractmethod
    def list_packages(self) -> V1Alpha1DriverPackageList:
        """
        List all available driver packages.
        """
        pass
