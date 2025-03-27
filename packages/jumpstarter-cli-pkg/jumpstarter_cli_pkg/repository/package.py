from importlib.metadata import Distribution, EntryPoint
from typing import Literal, Optional

from pydantic import Field

from jumpstarter.models import JsonBaseModel, ListBaseModel


class V1Alpha1AdapterEntryPoint(JsonBaseModel):
    """
    A Jumpstarter adapter entry point.
    """

    api_version: Literal["jumpstarter.dev/v1alpha1"] = Field(default="jumpstarter.dev/v1alpha1", alias="apiVersion")
    kind: Literal["AdapterEntryPoint"] = Field(default="AdapterEntryPoint")

    name: str
    type: str
    package: str

    @staticmethod
    def from_entry_point(ep: EntryPoint):
        return V1Alpha1AdapterEntryPoint(name=ep.name, type=ep.value.replace(":", "."), package=ep.dist.name)


class V1Alpha1DriverClientEntryPoint(JsonBaseModel):
    """
    A Jumpstarter driver client entry point.
    """

    api_version: Literal["jumpstarter.dev/v1alpha1"] = Field(default="jumpstarter.dev/v1alpha1", alias="apiVersion")
    kind: Literal["DriverClientEntryPoint"] = Field(default="DriverClientEntryPoint")

    name: str
    type: str
    package: str

    @staticmethod
    def from_entry_point(ep: EntryPoint):
        return V1Alpha1DriverClientEntryPoint(name=ep.name, type=ep.value.replace(":", "."), package=ep.dist.name)


class V1Alpha1DriverEntryPoint(JsonBaseModel):
    """
    A Jumpstarter driver entry point.
    """

    api_version: Literal["jumpstarter.dev/v1alpha1"] = Field(default="jumpstarter.dev/v1alpha1", alias="apiVersion")
    kind: Literal["DriverEntryPoint"] = Field(default="DriverEntryPoint")

    name: str
    type: str
    package: str

    @staticmethod
    def from_entry_point(ep: EntryPoint):
        return V1Alpha1DriverEntryPoint(name=ep.name, type=ep.value.replace(":", "."), package=ep.dist.name)


class V1Alpha1AdapterEntryPointList(ListBaseModel[V1Alpha1DriverEntryPoint]):
    """
    A list of Jumpstarter adapter list models.
    """

    kind: Literal["AdapterEntryPointList"] = Field(default="AdapterEntryPointList")


class V1Alpha1DriverEntryPointList(ListBaseModel[V1Alpha1DriverEntryPoint]):
    """
    A list of Jumpstarter driver list models.
    """

    kind: Literal["DriverEntryPointList"] = Field(default="DriverEntryPointList")


class V1Alpha1DriverClientEntryPointList(ListBaseModel[V1Alpha1DriverEntryPoint]):
    """
    A list of Jumpstarter driver client classes.
    """

    kind: Literal["DriverClientEntryPointList"] = Field(default="DriverClientEntryPointList")


class V1Alpha1DriverPackage(JsonBaseModel):
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
    installed: bool = True

    driver_clients: V1Alpha1DriverClientEntryPointList = Field(
        alias="driverClients", default=V1Alpha1DriverClientEntryPointList(items=[])
    )
    drivers: V1Alpha1DriverEntryPointList = V1Alpha1DriverEntryPointList(items=[])
    adapters: V1Alpha1AdapterEntryPointList = V1Alpha1AdapterEntryPointList(items=[])

    @staticmethod
    def requires_dist_to_categories(name: str, requires_dist: list[str]) -> list[str]:
        """
        Convert the `Requires-Dist` metadata to Jumpstarter driver categories.
        """
        categories = []
        # Check the package name
        match name:
            case "jumpstarter-driver-composite":
                categories.append("composite")
            case "jumpstarter-driver-network":
                categories.append("network")
            case "jumpstarter-driver-opendal":
                categories.append("storage")
            case "jumpstarter-driver-power":
                categories.append("power")
        # Check package dependencies
        for dist in requires_dist:
            if "jumpstarter-driver-composite" in dist and "composite" not in categories:
                categories.append("composite")
            elif "jumpstarter-driver-network" in dist and "network" not in categories:
                categories.append("network")
            elif "jumpstarter-driver-opendal" in dist and "storage" not in categories:
                categories.append("storage")
            elif "jumpstarter-driver-power" in dist and "power" not in categories:
                categories.append("power")

        return categories

    @staticmethod
    def from_distribution(dist: Distribution):
        """
        Create a `DriverPackage` from an `importlib.metadata.EntryPoint`.
        """
        return V1Alpha1DriverPackage(
            name=dist.name,
            categories=V1Alpha1DriverPackage.requires_dist_to_categories(
                dist.name, dist.metadata.get_all("Requires-Dist")
            ),
            version=dist.version,
            summary=dist.metadata.get("Summary"),
            license=dist.metadata.get("License"),
        )

    def list_drivers(self) -> V1Alpha1DriverEntryPointList:
        return self.drivers

    def list_driver_clients(self) -> V1Alpha1DriverClientEntryPointList:
        return self.driver_clients

    def list_adapters(self) -> V1Alpha1AdapterEntryPointList:
        return self.adapters


class V1Alpha1DriverPackageList(ListBaseModel[V1Alpha1DriverPackage]):
    """
    A list of Jumpstarter driver packages.
    """

    kind: Literal["DriverPackageList"] = Field(default="DriverPackageList")
