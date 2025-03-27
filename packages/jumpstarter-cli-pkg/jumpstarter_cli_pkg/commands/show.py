import asyncclick as click
from jumpstarter_cli_common import OutputMode, OutputType, opt_output_all
from jumpstarter_cli_common.exceptions import handle_exceptions
from jumpstarter_cli_pkg.repository import LocalDriverRepository


def print_package_details(package: str, drivers: bool, driver_clients: bool, adapters: bool, output: OutputType):
    flag_sum = sum([drivers, driver_clients, adapters])
    if flag_sum == 0:
        click.echo("Name: " + package.name)
        click.echo("Version: " + package.version)
        click.echo("Summary: " + (package.summary if package.summary else ""))
        click.echo("Categories: " + ", ".join(package.categories))
        click.echo("License: " + (package.license if package.license else ""))

    if flag_sum == 0 or drivers:
        click.echo("Drivers:")
        for driver in package.drivers.items:
            click.echo(f"  {driver.name}:")
            click.echo(f"    Name: {driver.name}")
            click.echo(f"    Type: {driver.type}")
    if flag_sum == 0 or driver_clients:
        click.echo("Driver Clients:")
        for driver_client in package.driver_clients.items:
            click.echo(f"  {driver_client.name}:")
            click.echo(f"    Name: {driver_client.name}")
            click.echo(f"    Type: {driver_client.type}")
    if flag_sum == 0 or adapters:
        click.echo("Adapters:")
        for adapter in package.adapters.items:
            click.echo(f"  {adapter.name}:")
            click.echo(f"    Name: {adapter.name}")
            click.echo(f"    Type: {adapter.type}")


@click.command("show")
@click.argument("package")
@click.option("--drivers", is_flag=True, help="Print drivers only.")
@click.option("--driver-clients", is_flag=True, help="Print driver clients only.")
@click.option("--adapters", is_flag=True, help="Print adapters only.")
@opt_output_all
@handle_exceptions
def show(package: str, drivers: bool, driver_clients: bool, adapters: bool, output: OutputType):
    """
    Show a Jumpstarter plugin package details.
    """
    # Add validation to ensure only one flag is set
    if sum([drivers, driver_clients, adapters]) > 1:
        raise click.UsageError("Only one of --drivers, --driver-clients, or --adapters can be specified.")

    local_repo = LocalDriverRepository.from_venv()
    local_package = local_repo.get_package(package)

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
            print_package_details(local_package, drivers, driver_clients, adapters, output)
