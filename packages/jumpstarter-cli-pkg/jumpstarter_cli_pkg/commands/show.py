import asyncclick as click
from jumpstarter_cli_common import OutputMode, OutputType, opt_output_all
from jumpstarter_cli_common.exceptions import handle_exceptions

from ..opt import opt_adapters, opt_driver_clients, opt_drivers, opt_inspect
from ..repository import LocalDriverRepository, V1Alpha1DriverPackage


def print_package_info(package: V1Alpha1DriverPackage):
    """Print basic package information."""
    click.echo("Name: " + package.name)
    click.echo("Version: " + package.version)
    click.echo("Summary: " + (package.summary if package.summary else ""))
    click.echo("Categories: " + ", ".join(package.categories))
    click.echo("License: " + (package.license if package.license else ""))


def print_drivers(package: V1Alpha1DriverPackage, inspect: bool):
    """Print drivers information."""
    click.echo("Drivers:")
    for driver in package.drivers.items:
        click.echo(f"  {driver.name}:")
        click.echo(f"    Module: {driver.module}")
        click.echo(f"    Class: {driver.class_name}")
        click.echo(f"    Type: {driver.type}")

        client_type_out = driver.client_type if driver.client_type else "(not available)"
        if not inspect:
            client_type_out = "(run this command with --inspect to see the client type)"
        click.echo(f"    Client: {client_type_out}")

        summary_out = driver.summary if driver.summary else "(not available)"
        if not inspect:
            summary_out = "(run this command with --inspect to see the summary)"
        click.echo(f"    Summary: {summary_out}")


def print_driver_clients(package: V1Alpha1DriverPackage, inspect: bool):
    """Print driver clients information."""
    click.echo("Driver Clients:")
    for driver_client in package.driver_clients.items:
        click.echo(f"  {driver_client.name}:")
        click.echo(f"    Module: {driver_client.module}")
        click.echo(f"    Class: {driver_client.class_name}")
        click.echo(f"    Type: {driver_client.type}")

        summary_out = driver_client.summary if driver_client.summary else "(not available)"
        if not inspect:
            summary_out = "(run this command with --inspect to see the summary)"
        click.echo(f"    Summary: {summary_out}")
        cli_out = "Yes" if driver_client.cli else "No"
        if not inspect:
            cli_out = "(run this command with --inspect to check if a CLI is available)"
        click.echo(f"    Has CLI: {cli_out}")


def print_adapters(package: V1Alpha1DriverPackage, inspect: bool):
    """Print adapters information."""
    click.echo("Adapters:")
    for adapter in package.adapters.items:
        click.echo(f"  {adapter.name}:")
        click.echo(f"    Module: {adapter.module}")
        click.echo(f"    Function: {adapter.function_name}")
        click.echo(f"    Type: {adapter.type}")
        summary_out = adapter.summary if adapter.summary else "(not available)"
        if not inspect:
            summary_out = "(run this command with --inspect to see the summary)"
        click.echo(f"    Summary: {summary_out}")


def print_package_details(
    package: V1Alpha1DriverPackage, drivers: bool, driver_clients: bool, adapters: bool, inspect: bool
):
    """Print package details based on the specified flags."""
    flag_sum = sum([drivers, driver_clients, adapters])

    if flag_sum == 0:
        print_package_info(package)

    if flag_sum == 0 or drivers:
        print_drivers(package, inspect)

    if flag_sum == 0 or driver_clients:
        print_driver_clients(package, inspect)

    if flag_sum == 0 or adapters:
        print_adapters(package, inspect)


@click.command("show")
@click.argument("package")
@opt_drivers
@opt_driver_clients
@opt_adapters
@opt_inspect
@opt_output_all
@handle_exceptions
def show(package: str, drivers: bool, driver_clients: bool, adapters: bool, output: OutputType, inspect: bool):
    """
    Show a Jumpstarter plugin package details.
    """
    # Add validation to ensure only one flag is set
    if sum([drivers, driver_clients, adapters]) > 1:
        raise click.UsageError("Only one of --drivers, --driver-clients, or --adapters can be specified.")

    local_repo = LocalDriverRepository.from_venv()
    local_package = local_repo.get_package(package, inspect)

    match output:
        case OutputMode.JSON:
            if drivers:
                click.echo(local_package.drivers.dump_json())
            elif driver_clients:
                click.echo(local_package.driver_clients.dump_json())
            elif adapters:
                click.echo(local_package.adapters.dump_json())
            else:
                click.echo(local_package.dump_json())
        case OutputMode.YAML:
            if drivers:
                click.echo(local_package.drivers.dump_yaml())
            elif driver_clients:
                click.echo(local_package.driver_clients.dump_yaml())
            elif adapters:
                click.echo(local_package.adapters.dump_yaml())
            else:
                click.echo(local_package.dump_yaml())
        case _:
            print_package_details(local_package, drivers, driver_clients, adapters, inspect)
