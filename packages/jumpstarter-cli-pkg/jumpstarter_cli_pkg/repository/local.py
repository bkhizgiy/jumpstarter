from importlib.metadata import entry_points

from .base import DriverRepository
from .package import (
    V1Alpha1AdapterEntryPoint,
    V1Alpha1DriverClientEntryPoint,
    V1Alpha1DriverEntryPoint,
    V1Alpha1DriverPackage,
    V1Alpha1DriverPackageList,
)


class LocalDriverRepository(DriverRepository):
    """
    A local repository of driver packages from the current venv.
    """

    DRIVER_ENTRY_POINT_GROUP = "jumpstarter.drivers"
    DRIVER_CLIENT_ENTRY_POINT_GROUP = "jumpstarter.clients"
    ADAPTER_ENTRY_POINT_GROUP = "jumpstarter.adapters"

    @staticmethod
    def from_venv():
        """
        Create a `LocalDriverRepository` from the current venv.
        """
        return LocalDriverRepository()

    def _get_driver_packages_from_entry_points(self) -> list[V1Alpha1DriverPackage]:
        # Create a dict of driver packages to collect entry points
        driver_packages: dict[str, V1Alpha1DriverPackage] = {}

        # Closure to process entry points for a specific entry point group
        def _process_entry_points(group: str):
            """Process entry points for a specific group and add them to driver_packages."""
            for entry_point in list(entry_points(group=group)):
                package_id = f"{entry_point.dist.name}=={entry_point.dist.version}"
                # Check if the package is in the driver packages
                if package_id not in driver_packages:
                    # Create a new package
                    if entry_point.dist is not None:
                        # Create the package from the entry point distribution metadata
                        driver_packages[package_id] = V1Alpha1DriverPackage.from_distribution(entry_point.dist)
                    else:
                        # Skip this entry point if the distribution metadata is not available
                        continue
                # Add the driver/client to the package
                match group:
                    case LocalDriverRepository.DRIVER_ENTRY_POINT_GROUP:
                        driver_packages[package_id].drivers.items.append(
                            V1Alpha1DriverEntryPoint.from_entry_point(entry_point)
                        )
                    case LocalDriverRepository.DRIVER_CLIENT_ENTRY_POINT_GROUP:
                        driver_packages[package_id].driver_clients.items.append(
                            V1Alpha1DriverClientEntryPoint.from_entry_point(entry_point)
                        )
                    case LocalDriverRepository.ADAPTER_ENTRY_POINT_GROUP:
                        driver_packages[package_id].adapters.items.append(
                            V1Alpha1AdapterEntryPoint.from_entry_point(entry_point)
                        )

        # Process driver entry points
        _process_entry_points(LocalDriverRepository.DRIVER_ENTRY_POINT_GROUP)

        # Process client entry points
        _process_entry_points(LocalDriverRepository.DRIVER_CLIENT_ENTRY_POINT_GROUP)

        # Process adapter entry points
        _process_entry_points(LocalDriverRepository.DRIVER_CLIENT_ENTRY_POINT_GROUP)

        # Return the assembled driver packages list
        return list(driver_packages.values())

    def list_packages(self) -> V1Alpha1DriverPackageList:
        # Get the local drivers using the Jumpstarter drivers entry point
        driver_packages = self._get_driver_packages_from_entry_points()
        return V1Alpha1DriverPackageList(items=driver_packages)
