import asyncclick as click
from jumpstarter_cli_common import OutputMode, OutputType, make_table, opt_config, opt_output_all
from jumpstarter_cli_common.exceptions import handle_exceptions

from .common import opt_selector
from jumpstarter.driver.repository import DriverPackageList, LocalDriverRepository


@click.group()
def get():
    """
    Display one or many resources.
    """


@get.command(name="exporters")
@opt_config(exporter=False)
@opt_selector
@opt_output_all
@handle_exceptions
def get_exporters(config, selector: str | None, output: OutputType):
    """
    Display one or many exporters
    """

    exporters = config.list_exporters(filter=selector)

    match output:
        case OutputMode.JSON:
            click.echo(exporters.dump_json())
        case OutputMode.YAML:
            click.echo(exporters.dump_yaml())
        case OutputMode.NAME:
            for exporter in exporters.exporters:
                click.echo(exporter.name)
        case _:
            columns = ["NAME", "LABELS"]
            rows = [
                {
                    "NAME": exporter.name,
                    "LABELS": ",".join(("{}={}".format(i[0], i[1]) for i in exporter.labels.items())),
                }
                for exporter in exporters.exporters
            ]
            click.echo(make_table(columns, rows))


@get.command(name="leases")
@opt_config(exporter=False)
@opt_selector
@opt_output_all
@handle_exceptions
def get_leases(config, selector: str | None, output: OutputType):
    """
    Display one or many leases
    """

    leases = config.list_leases(filter=selector)

    match output:
        case OutputMode.JSON:
            click.echo(leases.dump_json())
        case OutputMode.YAML:
            click.echo(leases.dump_yaml())
        case OutputMode.NAME:
            for lease in leases.leases:
                click.echo(lease.name)
        case _:
            columns = ["NAME", "CLIENT", "EXPORTER"]
            rows = [
                {
                    "NAME": lease.name,
                    "CLIENT": lease.client,
                    "EXPORTER": lease.exporter,
                }
                for lease in leases.leases
            ]
            click.echo(make_table(columns, rows))


MAX_SUMMARY_LENGTH = 40


def print_drivers(driver_packages: DriverPackageList, is_wide: bool):
    if is_wide:
        columns = ["NAME", "PACKAGE", "VERSION", "TYPE", "CATEGORIES", "LICENSE"]
    else:
        columns = ["NAME", "TYPE"]
    driver_rows = []
    for package in driver_packages.items:
        for driver in package.drivers:
            driver_rows.append(
                {
                    "NAME": driver.name,
                    "PACKAGE": package.name,
                    "VERSION": package.version,
                    "TYPE": driver.type,
                    "CATEGORIES": ",".join(package.categories),
                    "LICENSE": package.license if package.license else "Unspecified",
                }
            )
    click.echo(make_table(columns, driver_rows))


@get.command("drivers")
@opt_output_all
@handle_exceptions
async def get_drivers(output: OutputType):
    """
    Display all available drivers.
    """
    local_repo = LocalDriverRepository.from_venv()
    local_drivers = local_repo.list_packages()
    match output:
        case OutputMode.JSON:
            click.echo(local_drivers.dump_json())
        case OutputMode.YAML:
            click.echo(local_drivers.dump_yaml())
        case OutputMode.NAME:
            for package in local_drivers.items:
                for driver in package.drivers:
                    click.echo(f"driver.jumpstarter.dev/{package.name}/{driver.name}")
        case _:
            print_drivers(local_drivers, is_wide=output == OutputMode.WIDE)


def print_driver_clients(driver_packages: DriverPackageList, is_wide: bool):
    if is_wide:
        columns = ["NAME", "PACKAGE", "VERSION", "TYPE", "CATEGORIES", "LICENSE"]
    else:
        columns = ["NAME", "TYPE"]
    driver_rows = []
    for package in driver_packages.items:
        for client in package.clients:
            driver_rows.append(
                {
                    "NAME": client.name,
                    "PACKAGE": package.name,
                    "VERSION": package.version,
                    "TYPE": client.type,
                    "CATEGORIES": ",".join(package.categories),
                    "LICENSE": package.license if package.license else "Unspecified",
                }
            )
    click.echo(make_table(columns, driver_rows))


@get.command("driver-clients")
@opt_output_all
@handle_exceptions
async def get_driver_clients(output: OutputType):
    """
    Display all available driver clients.
    """
    local_repo = LocalDriverRepository.from_venv()
    local_drivers = local_repo.list_packages()
    match output:
        case OutputMode.JSON:
            click.echo(local_drivers.dump_json())
        case OutputMode.YAML:
            click.echo(local_drivers.dump_yaml())
        case OutputMode.NAME:
            for package in local_drivers.items:
                for driver in package.drivers:
                    click.echo(f"driver-client.jumpstarter.dev/{package.name}/{driver.name}")
        case _:
            print_driver_clients(local_drivers, is_wide=output == OutputMode.WIDE)


def print_packages(local_drivers: DriverPackageList, is_wide: bool):
    if is_wide:
        columns = ["NAME", "VERSION", "LICENSE", "CATEGORIES"]
    else:
        columns = ["NAME", "VERSION", "LICENSE", "CATEGORIES"]
    driver_rows = []
    for package in local_drivers.items:
        driver_rows.append(
            {
                "NAME": package.name,
                "VERSION": package.version,
                "CATEGORIES": ",".join(package.categories),
                "LICENSE": package.license if package.license else "Unspecified",
            }
        )
    click.echo(make_table(columns, driver_rows))


@get.command("packages")
@opt_output_all
@handle_exceptions
async def get_packages(output: OutputType):
    """
    Display all available jumpstarter driver packages.
    """
    local_repo = LocalDriverRepository.from_venv()
    local_drivers = local_repo.list_packages()
    match output:
        case OutputMode.JSON:
            click.echo(local_drivers.dump_json())
        case OutputMode.YAML:
            click.echo(local_drivers.dump_yaml())
        case OutputMode.NAME:
            for package in local_drivers.items:
                for driver in package.drivers:
                    click.echo(f"driver.jumpstarter.dev/{package.name}/{driver.name}")
        case _:
            print_packages(local_drivers, is_wide=output == OutputMode.WIDE)
