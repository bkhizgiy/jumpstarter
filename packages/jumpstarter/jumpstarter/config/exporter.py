from __future__ import annotations

from collections import OrderedDict, defaultdict
from contextlib import ExitStack, asynccontextmanager, contextmanager, suppress
from graphlib import TopologicalSorter
from pathlib import Path
from typing import Any, ClassVar, Literal, Optional, Self
from uuid import uuid4

import grpc  # type: ignore
import yaml  # type: ignore
from anyio.from_thread import start_blocking_portal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from .common import ObjectMeta
from .grpc import call_credentials
from .tls import TLSConfigV1Alpha1
from jumpstarter.client.base import DriverClient
from jumpstarter.common.grpc import aio_secure_channel, ssl_channel_credentials
from jumpstarter.common.importlib import import_class
from jumpstarter.driver import Driver


class ExporterConfigV1Alpha1DriverInstanceProxy(BaseModel):
    ref: str


class ExporterConfigV1Alpha1DriverInstanceComposite(BaseModel):
    children: dict[str, ExporterConfigV1Alpha1DriverInstance] = Field(default_factory=dict)


class ExporterConfigV1Alpha1DriverInstanceBase(BaseModel):
    type: str
    config: dict[str, Any] = Field(default_factory=dict)
    children: dict[str, ExporterConfigV1Alpha1DriverInstance] = Field(default_factory=dict)


class ExporterConfigV1Alpha1DriverInstance(RootModel):
    root: (
        ExporterConfigV1Alpha1DriverInstanceBase
        | ExporterConfigV1Alpha1DriverInstanceComposite
        | ExporterConfigV1Alpha1DriverInstanceProxy
    )

    def instantiate(self) -> Driver:
        match self.root:
            case ExporterConfigV1Alpha1DriverInstanceBase():
                driver_class = import_class(self.root.type, [], True)

                children = {name: child.instantiate() for name, child in self.root.children.items()}

                return driver_class(children=children, **self.root.config)

            case ExporterConfigV1Alpha1DriverInstanceComposite():
                from jumpstarter_driver_composite.driver import Composite

                children = {name: child.instantiate() for name, child in self.root.children.items()}

                return Composite(children=children)

            case ExporterConfigV1Alpha1DriverInstanceProxy():
                from jumpstarter_driver_composite.driver import Proxy

                return Proxy(ref=self.root.ref)

    @classmethod
    def from_path(cls, path: str) -> ExporterConfigV1Alpha1DriverInstance:
        with open(path) as f:
            return cls.model_validate(yaml.safe_load(f))

    @classmethod
    def from_str(cls, config: str) -> ExporterConfigV1Alpha1DriverInstance:
        return cls.model_validate(yaml.safe_load(config))


class ExporterConfigV1Alpha1(BaseModel):
    BASE_PATH: ClassVar[Path] = Path("/etc/jumpstarter/exporters")

    alias: str = Field(default="default")

    apiVersion: Literal["jumpstarter.dev/v1alpha1"] = Field(default="jumpstarter.dev/v1alpha1")
    kind: Literal["ExporterConfig"] = Field(default="ExporterConfig")
    metadata: ObjectMeta

    endpoint: str
    tls: TLSConfigV1Alpha1 = Field(default_factory=TLSConfigV1Alpha1)
    token: str
    grpcOptions: dict[str, str | int] | None = Field(default_factory=dict)

    export: dict[str, ExporterConfigV1Alpha1DriverInstance] = Field(default_factory=dict)

    path: Path | None = Field(default=None)

    @classmethod
    def _get_path(cls, alias: str):
        return (cls.BASE_PATH / alias).with_suffix(".yaml")

    @classmethod
    def exists(cls, alias: str):
        return cls._get_path(alias).exists()

    @classmethod
    def load_path(cls, path: Path):
        with path.open() as f:
            config = cls.model_validate(yaml.safe_load(f))
            config.path = path
            return config

    @classmethod
    def load(cls, alias: str) -> Self:
        config = cls.load_path(cls._get_path(alias))
        config.alias = alias
        return config

    @classmethod
    def list(cls) -> list[Self]:
        exporters = []
        with suppress(FileNotFoundError):
            for entry in cls.BASE_PATH.iterdir():
                exporters.append(cls.load(entry.stem))
        return exporters

    @classmethod
    def dump_yaml(self, config: Self) -> str:
        return yaml.safe_dump(config.model_dump(mode="json", exclude={"alias", "path"}), sort_keys=False)

    @classmethod
    def save(cls, config: Self, path: Optional[str] = None) -> Path:
        # Set the config path before saving
        if path is None:
            config.path = cls._get_path(config.alias)
            config.path.parent.mkdir(parents=True, exist_ok=True)
        else:
            config.path = Path(path)
        with config.path.open(mode="w") as f:
            yaml.safe_dump(config.model_dump(mode="json", exclude={"alias", "path"}), f, sort_keys=False)
        return config.path

    @classmethod
    def delete(cls, alias: str) -> Path:
        path = cls._get_path(alias)
        path.unlink(missing_ok=True)
        return path

    @asynccontextmanager
    async def serve_unix_async(self):
        # dynamic import to avoid circular imports
        from jumpstarter.exporter import Session

        with Session(
            root_device=ExporterConfigV1Alpha1DriverInstance(children=self.export).instantiate(),
        ) as session:
            async with session.serve_unix_async() as path:
                yield path

    @contextmanager
    def serve_unix(self):
        with start_blocking_portal() as portal:
            with portal.wrap_async_context_manager(self.serve_unix_async()) as path:
                yield path

    async def serve(self):
        # dynamic import to avoid circular imports
        from jumpstarter.exporter import Exporter

        async def channel_factory():
            credentials = grpc.composite_channel_credentials(
                await ssl_channel_credentials(self.endpoint, self.tls),
                call_credentials("Exporter", self.metadata, self.token),
            )
            return aio_secure_channel(self.endpoint, credentials, self.grpcOptions)

        async with Exporter(
            channel_factory=channel_factory,
            device_factory=ExporterConfigV1Alpha1DriverInstance(children=self.export).instantiate,
            tls=self.tls,
            grpc_options=self.grpcOptions,
        ) as exporter:
            await exporter.serve()

    def create_client_stub(self, allow: list[str] = None, unsafe: bool = False):
        """Create a client stub for this exporter without requiring a connection.

        This method generates a client stub by analyzing the exporter configuration
        instead of querying the exporter service. This is useful for documentation,
        intellisense, and testing purposes.

        Args:
            allow: List of allowed driver packages (default: empty list)
            unsafe: Whether to allow unsafe drivers (default: False)

        Returns:
            DriverClient: The client stub for the exporter
        """
        from jumpstarter.client import DriverClient

        # Use provided values or defaults
        allow = allow or []

        # Build a structure similar to what we'd get from GetReport
        topo = defaultdict(list)
        uuids = {}
        driver_info = {}
        clients = OrderedDict()
        stack = ExitStack()

        # Process driver instances and build the topology
        self._process_driver_instances(self.export, topo, uuids, driver_info)

        # Build clients in topological order
        self._build_client_stubs(topo, driver_info, clients, stack, allow, unsafe)

        # Return the root client (last one created)
        if clients:
            return clients.popitem(last=True)[1]
        else:
            # If no clients were created, return a base DriverClient
            from jumpstarter.client.base import DriverClient

            return DriverClient(
                uuid=uuid4(),
                labels={"jumpstarter.dev/name": "root"},
                channel=None,
                portal=None,
                stack=stack.enter_context(ExitStack()),
                children={},
            )

    def _process_driver_instances(
        self,
        instances: dict[str, ExporterConfigV1Alpha1DriverInstance],
        topo: dict[int, list[int]],
        uuids: dict[str, int],
        driver_info: dict[int, dict[str, Any]],
        parent_uuid: str | None = None,
    ):
        """Process driver instances to build topology and driver info.

        Args:
            instances: Dictionary of driver instances
            topo: Topology dictionary
            uuids: UUID to index mapping
            driver_info: Driver information dictionary
            parent_uuid: Parent UUID for hierarchical relationship
        """
        for name, instance in instances.items():
            # Generate a UUID for this instance
            instance_uuid = str(uuid4())
            instance_index = len(driver_info)

            # Track the UUID
            uuids[instance_uuid] = instance_index

            # Store parent relationship if exists
            if parent_uuid is not None:
                parent_index = uuids[parent_uuid]
                topo[parent_index].append(instance_index)

            # Extract the driver type
            if isinstance(instance.root, ExporterConfigV1Alpha1DriverInstanceBase):
                driver_type = instance.root.type
                # Record this driver's info (similar to report)
                driver_info[instance_index] = {
                    "uuid": instance_uuid,
                    "parent_uuid": parent_uuid or "",
                    "type": driver_type,
                    "name": name,
                }

                # Process any children
                if instance.root.children:
                    self._process_driver_instances(instance.root.children, topo, uuids, driver_info, instance_uuid)
            elif isinstance(instance.root, ExporterConfigV1Alpha1DriverInstanceComposite):
                # For composites, use a generic composite driver type
                driver_info[instance_index] = {
                    "uuid": instance_uuid,
                    "parent_uuid": parent_uuid or "",
                    "type": "jumpstarter_driver_composite.driver.Composite",
                    "name": name,
                }

                # Process children
                if instance.root.children:
                    self._process_driver_instances(instance.root.children, topo, uuids, driver_info, instance_uuid)
            elif isinstance(instance.root, ExporterConfigV1Alpha1DriverInstanceProxy):
                # For proxies, use the Proxy driver type
                driver_info[instance_index] = {
                    "uuid": instance_uuid,
                    "parent_uuid": parent_uuid or "",
                    "type": "jumpstarter_driver_composite.driver.Proxy",
                    "name": name,
                }

    def _build_client_stubs(
        self,
        topo: dict[int, list[int]],
        driver_info: dict[int, dict[str, Any]],
        clients: dict[int, DriverClient],
        stack: ExitStack,
        allow: list[str],
        unsafe: bool,
    ):
        """Build client stubs in topological order.

        Args:
            topo: Topology dictionary
            driver_info: Driver information dictionary
            clients: Client dictionary to populate
            stack: ExitStack for resource management
            allow: List of allowed driver packages
            unsafe: Whether to allow unsafe drivers
        """
        for index in TopologicalSorter(topo).static_order():
            driver = driver_info[index]

            # Determine the client class based on the driver type
            client_class = self._get_client_class_for_driver(driver["type"], allow, unsafe)

            # Create children dict for this client
            children = {}
            for child_index in topo[index]:
                child = driver_info[child_index]
                children[child["name"]] = clients[child_index]

            # Create the client instance
            client = client_class(
                uuid=uuid4(),
                labels={"jumpstarter.dev/name": driver["name"]},
                # We don't have a real channel, portal or stack, but we need the properties
                channel=None,
                portal=None,
                stack=stack.enter_context(ExitStack()),
                children=children,
            )

            clients[index] = client

    def _get_client_class_for_driver(self, driver_type, allow, unsafe):
        """Get the client class for a given driver type.

        Args:
            driver_type: Driver type string
            allow: List of allowed driver packages
            unsafe: Whether to allow unsafe drivers

        Returns:
            The client class to use
        """
        # Convert driver type to client package path
        driver_package = driver_type.split(".")
        if driver_package[0].endswith("_driver"):
            client_package = driver_package[0].replace("_driver", "_client") + ".client"
        else:
            # Use a default client if we can't determine the client package
            client_package = "jumpstarter.client.base.DriverClient"

        # Try to import the client class
        try:
            from jumpstarter.common.importlib import import_class

            return import_class(client_package, allow, unsafe)
        except ImportError:
            # Fallback to base DriverClient
            from jumpstarter.client.base import DriverClient

            return DriverClient


class ExporterConfigListV1Alpha1(BaseModel):
    api_version: Literal["jumpstarter.dev/v1alpha1"] = Field(alias="apiVersion", default="jumpstarter.dev/v1alpha1")
    items: list[ExporterConfigV1Alpha1]
    kind: Literal["ExporterConfigList"] = Field(default="ExporterConfigList")

    def dump_json(self):
        return self.model_dump_json(indent=4, by_alias=True)

    def dump_yaml(self):
        return yaml.safe_dump(self.model_dump(mode="json", by_alias=True), indent=2)

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True)
