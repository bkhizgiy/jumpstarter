from abc import ABC, abstractmethod
from importlib.metadata import EntryPoint, entry_points
from typing import Literal, Optional

from pydantic import Field

from jumpstarter.models import JsonBaseModel, ListBaseModel


class DriverClientEntryPoint(JsonBaseModel):
    """
    A Jumpstarter driver client entry point.
    """

    name: str
    type: str

    @staticmethod
    def from_entry_point(ep: EntryPoint):
        return DriverClientEntryPoint(name=ep.name, type=ep.value.replace(":", "."))


class DriverEntryPoint(JsonBaseModel):
    """
    A Jumpstarter driver entry point.
    """

    name: str
    type: str

    @staticmethod
    def from_entry_point(ep: EntryPoint):
        return DriverEntryPoint(name=ep.name, type=ep.value.replace(":", "."))


class DriverPackage(JsonBaseModel):
    """
    A Jumpstarter driver package.
    """

    api_version: Literal["jumpstarter.dev/v1alpha1"] = Field(default="jumpstarter.dev/v1alpha1", alias="apiVersion")
    kind: Literal["DriverPackage"] = Field(default="DriverPackage")
    name: str
    version: str
    categories: list[str] = []
    summary: Optional[str] = None
    license: Optional[str] = None

    clients: list[DriverClientEntryPoint] = []
    drivers: list[DriverEntryPoint] = []

    @staticmethod
    def requires_dist_to_categories(requires_dist: list[str]) -> list[str]:
        """
        Convert the `Requires-Dist` metadata to Jumpstarter driver categories.
        """
        categories = []
        for dist in requires_dist:
            if "jumpstarter-driver-network" in dist:
                categories.append("network")
            elif "jumpstarter-driver-opendal" in dist:
                categories.append("storage")
            elif "jumpstarter-driver-power" in dist:
                categories.append("power")

        return categories

    @staticmethod
    def from_entry_point(ep: EntryPoint):
        """
        Create a `DriverPackage` from an `importlib.metadata.EntryPoint`.
        """
        return DriverPackage(
            name=ep.name,
            package=ep.dist.name,
            type=ep.value.replace(":", "."),
            categories=DriverPackage.requires_dist_to_categories(ep.dist.metadata.get_all("Requires-Dist")),
            version=ep.dist.version,
            summary=ep.dist.metadata.get("Summary"),
            license=ep.dist.metadata.get("License"),
        )


class DriverPackageList(ListBaseModel[DriverPackage]):
    """
    A list of Jumpstarter driver packages.
    """

    kind: Literal["DriverPackageList"] = Field(default="DriverPackageList")


class DriverList(ListBaseModel[DriverEntryPoint]):
    """
    A list of Jumpstarter driver list models.
    """

    kind: Literal["DriverList"] = Field(default="DriverList")


class DriverClientList(ListBaseModel[DriverEntryPoint]):
    """
    A list of Jumpstarter driver client classes.
    """

    kind: Literal["DriverClientList"] = Field(default="DriverClientList")


class DriverRepository(ABC):
    """
    A repository of driver packages.
    """

    @abstractmethod
    def list_packages(self) -> DriverPackageList:
        """
        List all available driver packages.
        """
        pass


class LocalDriverRepository(DriverRepository):
    """
    A local repository of driver packages from the current venv.
    """

    DRIVER_ENTRY_POINT_GROUP = "jumpstarter.drivers"
    DRIVER_CLIENT_ENTRY_POINT_GROUP = "jumpstarter.clients"

    @staticmethod
    def from_venv():
        """
        Create a `LocalDriverRepository` from the current venv.
        """
        return LocalDriverRepository()

    def _get_driver_packages_from_entry_points(self) -> list[DriverPackage]:
        # Create a dict of driver packages to collect entry points
        driver_packages: dict[str, DriverPackage] = {}

        # Closure to process entry points for a specific entry point group
        def _process_entry_points(group: str, is_driver: bool = True):
            """Process entry points for a specific group and add them to driver_packages."""
            for entry_point in list(entry_points(group=group)):
                package_id = f"{entry_point.dist.name}=={entry_point.dist.version}"
                # Check if the package is in the driver packages
                if package_id not in driver_packages:
                    # Create a new package
                    driver_packages[package_id] = DriverPackage.from_entry_point(entry_point)
                # Add the driver/client to the package
                if is_driver:
                    driver_packages[package_id].drivers.append(DriverEntryPoint.from_entry_point(entry_point))
                else:
                    driver_packages[package_id].clients.append(DriverClientEntryPoint.from_entry_point(entry_point))

        # Process driver entry points
        _process_entry_points(LocalDriverRepository.DRIVER_ENTRY_POINT_GROUP, is_driver=True)

        # Process client entry points
        _process_entry_points(LocalDriverRepository.DRIVER_CLIENT_ENTRY_POINT_GROUP, is_driver=False)

        # Return the assembled driver packages
        return list(driver_packages.values())

    def list_packages(self) -> DriverPackageList:
        # Get the local drivers using the Jumpstarter drivers entry point
        driver_packages = self._get_driver_packages_from_entry_points()
        return DriverPackageList(items=driver_packages)
