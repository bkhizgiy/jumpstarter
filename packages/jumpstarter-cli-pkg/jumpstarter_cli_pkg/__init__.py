import asyncclick as click
from jumpstarter_cli_common import AliasedGroup

from .commands.list import list


@click.group(cls=AliasedGroup)
def pkg():
    """Jumpstarter package management CLI tool"""


pkg.add_command(list)

if __name__ == "__main__":
    pkg()
