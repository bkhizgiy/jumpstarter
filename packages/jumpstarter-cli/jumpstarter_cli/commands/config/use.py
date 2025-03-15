import asyncclick as click
from jumpstarter_cli_common import (
    OutputMode,
    PathOutputType,
    opt_output_path_only,
)
from jumpstarter_cli_common.exceptions import handle_exceptions

from jumpstarter.config import (
    UserConfigV1Alpha1,
)


@click.group()
def use():
    """
    Select the current config to use as default.
    """


@use.command("client")
@click.argument("alias", type=str)
@opt_output_path_only
@handle_exceptions
def use_client_config(alias: str, output: PathOutputType):
    """Select a client config to use as default."""
    user_config = UserConfigV1Alpha1.load_or_create()
    path = user_config.use_client(alias)
    if output == OutputMode.PATH:
        click.echo(path)
