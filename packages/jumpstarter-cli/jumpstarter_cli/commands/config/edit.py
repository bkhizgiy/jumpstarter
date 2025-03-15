import asyncclick as click
from jumpstarter_cli_common import AliasedGroup, arg_alias

from jumpstarter.config import ClientConfigV1Alpha1, ExporterConfigV1Alpha1


@click.group(cls=AliasedGroup)
def edit():
    """Edit Jumpstarter configuration files in your default editor."""


@edit.command("exporter")
@arg_alias
def edit_exporter_config(alias):
    """Edit an exporter config."""
    try:
        config = ExporterConfigV1Alpha1.load(alias)
    except FileNotFoundError as err:
        raise click.ClickException(f'Exporter "{alias}" does not exist') from err
    click.edit(filename=config.path)


@edit.command("client")
@arg_alias
def edit_client_config(alias):
    """Edit a client config."""
    try:
        config = ClientConfigV1Alpha1.load(alias)
    except FileNotFoundError as err:
        raise click.ClickException(f'Client "{alias}" does not exist') from err
    click.edit(filename=config.path)
