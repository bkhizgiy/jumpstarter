import asyncclick as click
from jumpstarter_cli_common import OutputType, opt_output_all
from jumpstarter_cli_common.exceptions import handle_exceptions
from jumpstarter_cli_pkg.repository import LocalDriverRepository


@click.command("show")
@click.argument("package")
@click.option("--drivers", is_flag=True, help="Print drivers only.")
@click.option("--driver-clients", is_flag=True, help="Print driver clients only.")
@click.option("--adapters", is_flag=True, help="Print adapters only.")
@opt_output_all
@handle_exceptions
def show(package: str, drivers: bool, driver_clients: bool, adapters: bool, output: OutputType):
    local_repo = LocalDriverRepository.from_venv()
    local_package = local_repo.get_package(package)
    click.echo("Name: " + local_package.name)
    click.echo("Version: " + local_package.version)
    click.echo("Summary: " + (local_package.summary if local_package.summary else ""))
    click.echo("Categories: " + ", ".join(local_package.categories))
    click.echo("License: " + (local_package.license if local_package.license else ""))
    click.echo("Drivers:")
    for driver in local_package.drivers.items:
        click.echo(f"  {driver.name}:")
        click.echo(f"    Name: {driver.name}")
        click.echo(f"    Type: {driver.type}")
    click.echo("Driver Clients:")
    for driver_client in local_package.driver_clients.items:
        click.echo(f"  {driver_client.name}:")
        click.echo(f"    Name: {driver_client.name}")
        click.echo(f"    Type: {driver_client.type}")
    click.echo("Adapters:")
    for adapter in local_package.adapters.items:
        click.echo(f"  {driver_client.name}:")
        click.echo(f"    Name: {adapter.name}")
        click.echo(f"    Type: {adapter.type}")
