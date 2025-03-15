import asyncclick as click
from jumpstarter_cli_client import client
from jumpstarter_cli_common import AliasedGroup, version
from jumpstarter_cli_driver import driver
from jumpstarter_cli_exporter import exporter

from .commands import create, delete, get, import_res, install


@click.group(cls=AliasedGroup)
def jmp():
    """The Jumpstarter CLI"""


jmp.add_command(create)
jmp.add_command(delete)
jmp.add_command(get)
jmp.add_command(import_res)
jmp.add_command(install)
jmp.add_command(client)
jmp.add_command(driver)
jmp.add_command(exporter)
jmp.add_command(version)

if __name__ == "__main__":
    jmp()
