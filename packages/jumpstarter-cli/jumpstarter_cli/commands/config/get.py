from typing import Optional

import asyncclick as click
from jumpstarter_cli_common import (
    AliasedGroup,
    OutputMode,
    OutputType,
    make_table,
    opt_output_all,
)
from jumpstarter_cli_common.exceptions import handle_exceptions

from jumpstarter.config import (
    ClientConfigListV1Alpha1,
    ClientConfigV1Alpha1,
    ExporterConfigListV1Alpha1,
    ExporterConfigV1Alpha1,
    UserConfigV1Alpha1,
)


@click.group(cls=AliasedGroup)
def get():
    """Get Jumpstarter configuration files."""


CLIENT_CONFIG_COLUMNS = ["CURRENT", "NAME", "ENDPOINT", "PATH"]
EXPORTER_CONFIG_COLUMNS = ["ALIAS", "PATH"]


def make_client_config_row(c: ClientConfigV1Alpha1, current_name: str):
    return {
        "CURRENT": "*" if current_name == c.alias else "",
        "NAME": c.alias,
        "ENDPOINT": c.endpoint,
        "PATH": str(c.path),
    }


def get_client_config(alias: Optional[str], output: OutputType, current_name: Optional[str]):
    try:
        config = ClientConfigV1Alpha1.load(alias)
        match output:
            case OutputMode.JSON:
                click.echo(ClientConfigV1Alpha1.dump_json(config))
            case OutputMode.YAML:
                click.echo(ClientConfigV1Alpha1.dump_yaml(config))
            case OutputMode.NAME:
                click.echo(f"client-config.jumpstarter.dev/{config.alias}")
            case _:
                click.echo(make_table(CLIENT_CONFIG_COLUMNS, [make_client_config_row(config, current_name)]))
    except FileNotFoundError as err:
        raise click.ClickException(f'Client "{alias}" does not exist') from err


def get_client_configs(output: OutputType, current_name: Optional[str]):
    configs = ClientConfigV1Alpha1.list()
    match output:
        case OutputMode.JSON:
            click.echo(ClientConfigListV1Alpha1(current_config=current_name, items=configs).dump_json())
        case OutputMode.YAML:
            click.echo(ClientConfigListV1Alpha1(current_config=current_name, items=configs).dump_yaml())
        case OutputMode.NAME:
            if len(configs) > 0:
                click.echo(f"client-config.jumpstarter.dev/{configs[0].alias}")
        case _:
            rows = [make_client_config_row(client, current_name) for client in configs]
            click.echo(make_table(CLIENT_CONFIG_COLUMNS, rows))


@get.command("client")
@click.argument("alias", type=str, required=False, default=None)
@opt_output_all
@handle_exceptions
def get_client(alias: Optional[str], output: OutputType):
    current_name = None
    if UserConfigV1Alpha1.exists():
        current_client = UserConfigV1Alpha1.load().config.current_client
        current_name = current_client.alias if current_client is not None else None

    if alias is None:
        get_client_configs(output, current_name)
    else:
        get_client_config(alias, output, current_name)


def make_exporter_config_row(exporter: ExporterConfigV1Alpha1):
    return {
        "ALIAS": exporter.alias,
        "PATH": str(exporter.path),
    }


def get_exporter_config(alias: Optional[str], output: OutputType):
    try:
        config = ExporterConfigV1Alpha1.load(alias)
        match output:
            case OutputMode.JSON:
                click.echo(ExporterConfigV1Alpha1.dump_json(config))
            case OutputMode.YAML:
                click.echo(ExporterConfigV1Alpha1.dump_yaml(config))
            case OutputMode.NAME:
                click.echo(f"exporter-config.jumpstarter.dev/{config.alias}")
            case _:
                click.echo(make_table(EXPORTER_CONFIG_COLUMNS, [make_exporter_config_row(config)]))
    except FileNotFoundError as err:
        raise click.ClickException(f'Client "{alias}" does not exist') from err


def get_exporter_configs(output: OutputType):
    configs = ExporterConfigV1Alpha1.list()
    match output:
        case OutputMode.JSON:
            click.echo(ExporterConfigListV1Alpha1(items=configs).dump_json())
        case OutputMode.YAML:
            click.echo(ExporterConfigListV1Alpha1(items=configs).dump_yaml())
        case OutputMode.NAME:
            if len(configs) > 0:
                click.echo(f"exporter-config.jumpstarter.dev/{configs[0].alias}")
        case _:
            rows = list(map(make_exporter_config_row, configs))
            click.echo(make_table(EXPORTER_CONFIG_COLUMNS, rows))


@get.command("exporter")
@click.argument("alias", type=str, required=False, default=None)
@opt_output_all
@handle_exceptions
def get_exporter(alias: Optional[str], output: OutputType):
    if alias is None:
        get_exporter_configs(output)
    else:
        get_exporter_config(alias, output)
