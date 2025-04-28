from collections import OrderedDict, defaultdict
from contextlib import asynccontextmanager
from functools import reduce
from graphlib import TopologicalSorter
from uuid import UUID

import grpc
from google.protobuf import empty_pb2
from jumpstarter_protocol import jumpstarter_pb2, jumpstarter_pb2_grpc
from pydantic.dataclasses import ConfigDict, dataclass

from jumpstarter.common.exceptions import ConfigurationError
from jumpstarter.driver import Driver


class CompositeInterface:
    @classmethod
    def client(cls) -> str:
        return "jumpstarter_driver_composite.client.CompositeClient"


@dataclass(kw_only=True)
class Composite(CompositeInterface, Driver):
    pass


@dataclass(kw_only=True)
class Proxy(Driver):
    ref: str

    @classmethod
    def client(cls) -> str:
        return "jumpstarter.client.DriverClient"  # unused

    def __target(self, root, name):
        try:
            path = self.ref.split(".")
            if not path:
                raise ConfigurationError(f"Proxy driver {name} has empty path")
            return reduce(lambda instance, name: instance.children[name], path, root)
        except KeyError:
            raise ConfigurationError(f"Proxy driver {name} references nonexistent driver {self.ref}") from None

    def report(self, *, root=None, parent=None, name=None):
        return self.__target(root, name).report(root=root, parent=parent, name=name)

    def enumerate(self, *, root=None, parent=None, name=None):
        return self.__target(root, name).enumerate(root=root, parent=parent, name=name)


@dataclass(kw_only=True, config=ConfigDict(arbitrary_types_allowed=True))
class ExternalStub(Driver):
    target: str
    report_: jumpstarter_pb2.DriverInstanceReport

    def client(self) -> str:
        return self.report_.labels["jumpstarter.dev/client"]


@dataclass(kw_only=True)
class External(Driver):
    target: str

    def __post_init__(self):
        if hasattr(super(), "__post_init__"):
            super().__post_init__()

        self.channel = grpc.aio.insecure_channel(self.target)
        self.stub = jumpstarter_pb2_grpc.ExporterServiceStub(self.channel)

    def close(self):
        for child in self.children.values():
            child.close()

    def reset(self):
        for child in self.children.values():
            child.reset()

    @classmethod
    def client(cls) -> str:
        pass

    def extra_labels(self) -> dict[str, str]:
        pass

    async def DriverCall(self, request, context):
        pass

    async def StreamingDriverCall(self, request, context):
        pass

    @asynccontextmanager
    async def Stream(self, request, context):
        pass

    def report(self, *, root=None, parent=None, name=None):
        channel = grpc.insecure_channel(self.target)
        stub = jumpstarter_pb2_grpc.ExporterServiceStub(channel)
        response = stub.GetReport(empty_pb2.Empty())
        return response.reports[0]

    def enumerate(self, *, root=None, parent=None, name=None):
        channel = grpc.insecure_channel(self.target)
        stub = jumpstarter_pb2_grpc.ExporterServiceStub(channel)
        response = stub.GetReport(empty_pb2.Empty())

        topo = defaultdict(list)
        last_seen = {}
        reports = {}
        instances = OrderedDict()

        for index, report in enumerate(response.reports):
            topo[index] = []

            last_seen[report.uuid] = index

            if report.parent_uuid != "":
                parent_index = last_seen[report.parent_uuid]
                topo[parent_index].append(index)

            reports[index] = report

        for index in TopologicalSorter(topo).static_order():
            report = reports[index]

            instance = ExternalStub(
                uuid=UUID(report.uuid),
                labels=report.labels,
                children={reports[k].labels["jumpstarter.dev/name"]: instances[k] for k in topo[index]},
                report_=report,
                target=self.target,
            )

            instances[index] = instance

        return instances.popitem(last=True)[1].enumerate(root=root, parent=parent, name=name)

    @asynccontextmanager
    async def resource(self, handle: str, timeout: int = 300):
        pass
