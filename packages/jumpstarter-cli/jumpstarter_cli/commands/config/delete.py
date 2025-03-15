import asyncclick as click
from jumpstarter_cli_common import (
    AliasedGroup,
    OutputMode,
    PathOutputType,
    arg_alias,
    opt_output_path_only,
)
from jumpstarter_cli_common.exceptions import handle_exceptions

from .util import set_next_client
from jumpstarter.config import ClientConfigV1Alpha1, ExporterConfigV1Alpha1


@click.group(cls=AliasedGroup)
def delete():
    """Delete Jumpstarter configuration files."""


@delete.command("exporter")
@arg_alias
@opt_output_path_only
@handle_exceptions
def delete_exporter_config(alias, output: PathOutputType):
    """Delete an exporter config."""
    try:
        ExporterConfigV1Alpha1.load(alias)
    except FileNotFoundError as err:
        raise click.ClickException(f'exporter "{alias}" does not exist') from err
    path = ExporterConfigV1Alpha1.delete(alias)
    if output == OutputMode.PATH:
        click.echo(path)


@delete.command("client")
@click.argument("name", type=str)
@opt_output_path_only
@handle_exceptions
def delete_client_config(name: str, output: PathOutputType):
    """Delete a client config."""
    set_next_client(name)
    path = ClientConfigV1Alpha1.delete(name)
    if output == OutputMode.PATH:
        click.echo(path)
