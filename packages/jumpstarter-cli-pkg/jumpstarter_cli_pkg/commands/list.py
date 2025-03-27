import re
from typing import Optional

import asyncclick as click
from jumpstarter_cli_common import opt_output_all
from jumpstarter_cli_common.exceptions import handle_exceptions
from jumpstarter_cli_common.opt import OutputMode, OutputType
from jumpstarter_cli_common.table import make_table

from ..repository import LocalDriverRepository, V1Alpha1DriverPackageList

MAX_SUMMARY_LENGTH = 100


def clean_truncate_summary(summary: Optional[str]):
    if summary is None:
        return ""
    # Get only the first line
    first_line = summary.split("\n")[0].strip()
    # Strip markdown formatting
    cleaned_summary = re.sub(r"[#*_~`\[\]\(\)\{}]", "", first_line)  # Remove markdown characters
    # Truncate if necessary
    truncated_summary = cleaned_summary[:MAX_SUMMARY_LENGTH] + (
        "..." if len(cleaned_summary) > MAX_SUMMARY_LENGTH else ""
    )
    return truncated_summary


def print_packages(local_drivers: V1Alpha1DriverPackageList, is_wide: bool):
    if is_wide:
        columns = ["NAME", "VERSION", "INSTALLED", "CATEGORIES", "LICENSE", "SUMMARY"]
    else:
        columns = ["NAME", "VERSION", "INSTALLED", "CATEGORIES"]
    driver_rows = []
    for package in local_drivers.items:
        driver_rows.append(
            {
                "INSTALLED": "*" if package.installed else "",
                "NAME": package.name,
                "VERSION": package.version,
                "CATEGORIES": ",".join(package.categories),
                "LICENSE": package.license if package.license else "Unspecified",
                "SUMMARY": clean_truncate_summary(package.summary),
            }
        )
    click.echo(make_table(columns, driver_rows))


@click.command("list")
@opt_output_all
@handle_exceptions
def list(output: OutputType):
    """List Jumpstarter packages"""
    local_repo = LocalDriverRepository.from_venv()
    local_drivers = local_repo.list_packages()
    match output:
        case OutputMode.JSON:
            click.echo(local_drivers.dump_json())
        case OutputMode.YAML:
            click.echo(local_drivers.dump_yaml())
        case OutputMode.NAME:
            for package in local_drivers.items:
                for driver in package.drivers.items:
                    click.echo(f"driver.jumpstarter.dev/{package.name}/{driver.name}")
        case _:
            click.echo("Fetching local packages for current Python environment")
            print_packages(local_drivers, is_wide=output == OutputMode.WIDE)


# def print_drivers(driver_packages: V1Alpha1DriverPackageList, is_wide: bool):
#     if is_wide:
#         columns = ["NAME", "PACKAGE", "VERSION", "TYPE", "CATEGORIES", "LICENSE"]
#     else:
#         columns = ["NAME", "TYPE"]
#     driver_rows = []
#     for package in driver_packages.items:
#         for driver in package.drivers:
#             driver_rows.append(
#                 {
#                     "NAME": driver.name,
#                     "PACKAGE": package.name,
#                     "VERSION": package.version,
#                     "TYPE": driver.type,
#                     "CATEGORIES": ",".join(package.categories),
#                     "LICENSE": package.license if package.license else "Unspecified",
#                 }
#             )
#     click.echo(make_table(columns, driver_rows))


# @list.command("drivers")
# @opt_output_all
# @handle_exceptions
# async def get_drivers(output: OutputType):
#     """
#     Display all available drivers.
#     """
#     local_repo = LocalDriverRepository.from_venv()
#     local_drivers = local_repo.list_packages()
#     match output:
#         case OutputMode.JSON:
#             click.echo(local_drivers.dump_json())
#         case OutputMode.YAML:
#             click.echo(local_drivers.dump_yaml())
#         case OutputMode.NAME:
#             for package in local_drivers.items:
#                 for driver in package.drivers:
#                     click.echo(f"driver.jumpstarter.dev/{package.name}/{driver.name}")
#         case _:
#             print_drivers(local_drivers, is_wide=output == OutputMode.WIDE)


# def print_driver_clients(driver_packages: V1Alpha1DriverPackageList, is_wide: bool):
#     if is_wide:
#         columns = ["NAME", "PACKAGE", "VERSION", "TYPE", "CATEGORIES", "LICENSE"]
#     else:
#         columns = ["NAME", "TYPE"]
#     driver_rows = []
#     for package in driver_packages.items:
#         for client in package.clients:
#             driver_rows.append(
#                 {
#                     "NAME": client.name,
#                     "PACKAGE": package.name,
#                     "VERSION": package.version,
#                     "TYPE": client.type,
#                     "CATEGORIES": ",".join(package.categories),
#                     "LICENSE": package.license if package.license else "Unspecified",
#                 }
#             )
#     click.echo(make_table(columns, driver_rows))


# @list.command("driver-clients")
# @opt_output_all
# @handle_exceptions
# async def get_driver_clients(output: OutputType):
#     """
#     Display all available driver clients.
#     """
#     local_repo = LocalDriverRepository.from_venv()
#     local_drivers = local_repo.list_packages()
#     match output:
#         case OutputMode.JSON:
#             click.echo(local_drivers.dump_json())
#         case OutputMode.YAML:
#             click.echo(local_drivers.dump_yaml())
#         case OutputMode.NAME:
#             for package in local_drivers.items:
#                 for driver in package.drivers:
#                     click.echo(f"driver-client.jumpstarter.dev/{package.name}/{driver.name}")
#         case _:
#             print_driver_clients(local_drivers, is_wide=output == OutputMode.WIDE)


# @list.command("packages")
# async def get_packages(output: OutputType):
#     """
#     Display all available jumpstarter driver packages.
#     """
