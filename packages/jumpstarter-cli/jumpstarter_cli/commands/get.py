import logging
from typing import Optional

import asyncclick as click
from jumpstarter_cli_common import (
    AliasedGroup,
    OutputType,
    opt_context,
    opt_kubeconfig,
    opt_log_level,
    opt_namespace,
    opt_output_all,
)
from jumpstarter_cli_common.exceptions import async_handle_k8s_exceptions
from jumpstarter_kubernetes import (
    ClientsV1Alpha1Api,
    ExportersV1Alpha1Api,
    LeasesV1Alpha1Api,
)

from ..print import print_client, print_clients, print_exporter, print_exporters, print_lease, print_leases


@click.group(cls=AliasedGroup)
@opt_log_level
def get(log_level: Optional[str]):
    """Get available Jumpstarter Kubernetes objects"""
    if log_level:
        logging.basicConfig(level=log_level.upper())
    else:
        logging.basicConfig(level=logging.INFO)


@get.command("client")
@click.argument("name", type=str, required=False, default=None)
@opt_namespace
@opt_kubeconfig
@opt_context
@opt_output_all
@async_handle_k8s_exceptions
async def get_client(
    name: Optional[str], kubeconfig: Optional[str], context: Optional[str], namespace: str, output: OutputType
):
    """Get the client objects in a Kubernetes cluster"""
    async with ClientsV1Alpha1Api(namespace, kubeconfig, context) as api:
        if name is not None:
            client = await api.get_client(name)
            print_client(client, output)
        else:
            clients = await api.list_clients()
            print_clients(clients, namespace, output)


@get.command("exporter")
@click.argument("name", type=str, required=False, default=None)
@opt_namespace
@opt_kubeconfig
@opt_context
@opt_output_all
@click.option("-d", "--devices", is_flag=True, help="Display the devices hosted by the exporter(s)")
@async_handle_k8s_exceptions
async def get_exporter(
    name: Optional[str],
    kubeconfig: Optional[str],
    context: Optional[str],
    namespace: str,
    devices: bool,
    output: OutputType,
):
    """Get the exporter objects in a Kubernetes cluster"""
    async with ExportersV1Alpha1Api(namespace, kubeconfig, context) as api:
        if name is not None:
            exporter = await api.get_exporter(name)
            print_exporter(exporter, devices, output)
        else:
            exporters = await api.list_exporters()
            print_exporters(exporters, namespace, devices, output)


@get.command("lease")
@click.argument("name", type=str, required=False, default=None)
@opt_namespace
@opt_kubeconfig
@opt_context
@opt_output_all
@async_handle_k8s_exceptions
async def get_lease(
    name: Optional[str], kubeconfig: Optional[str], context: Optional[str], namespace: str, output: OutputType
):
    """Get the lease objects in a Kubernetes cluster"""
    async with LeasesV1Alpha1Api(namespace, kubeconfig, context) as api:
        if name is not None:
            lease = await api.get_lease(name)
            print_lease(lease, output)
        else:
            leases = await api.list_leases()
            print_leases(leases, namespace, output)
