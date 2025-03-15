import asyncclick as click
from jumpstarter_cli_common.alias import AliasedGroup

from .create import create
from .delete import delete
from .edit import edit
from .get import get
from .use import use

__all__ = []


@click.group(cls=AliasedGroup)
def config():
    """
    Manage Jumpstarter configuration files.
    """


config.add_command(create)
config.add_command(delete)
config.add_command(edit)
config.add_command(get)
config.add_command(use)
