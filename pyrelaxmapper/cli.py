# -*- coding: utf-8 -*-
"""Application cli interface."""
import click
import logging

from pyrelaxmapper import __version__, commands
from pyrelaxmapper.commands import Action

logger = logging.getLogger()


def abort_if_false(ctx, param, value):
    """Abort click if answered no."""
    if not value:
        ctx.abort()


def echo_help(command):
    """Print help for click command."""
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


def validate_actions(ctx, param, values):
    """Validate actions argument and parse actions."""
    try:
        return commands.parse_actions(values)
    except ValueError:
        actions = ', '.join(e.value for e in Action)
        wrong = [value for value in values if value not in actions]
        multiple = '' if len(wrong) <= 1 else 's'
        wrong = ', '.join(wrong)
        raise click.BadParameter('invalid choice{}: {}. (choose from {})'
                                 .format(multiple, wrong, actions))


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


@main.command()
@click.argument('actions', callback=validate_actions, nargs=-1)
@click.option('conf_file', '-c', envvar='RLCONF', type=click.File(), help='Configuration file.')
def make(actions, conf_file):
    """Make target ACTIONS in correct order. Chainable.

    \b
    ACTIONS:
      clean    Clean all caches.
      relax    Run RL algorithm and save results.
      stats    Create statistics report.
    """
    if not actions:
        echo_help(make)
        return
    # Remove these logs. Now just for test.
    logger.info('Start.')

    config = commands.config_load(conf_file)

    if Action.Clean in actions:
        commands.config_clean(config)

    status = None
    if Action.Relax in actions:
        # could merge
        relaxer = commands.relaxer_load(config)
        status = commands.relaxer_relax(relaxer)

    # Maybe should be able to pass status file!
    if Action.Stats in actions:
        commands.relaxer_stats(status, config)

    logger.info('End.')


@main.group('config')
def config_group():
    """Configuration utilities."""
    pass


@config_group.command('list')
def config_list():
    """List merged application configuration."""
    commands.config_list()


@config_group.command('reset')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to reset config?')
def config_reset():
    """Set user config file to defaults."""
    commands.config_reset()


@config_group.command('edit')
def config_edit():
    """Edit user config file."""
    if not commands.config_exists():
        commands.config_reset()

    click.edit(filename=commands.config_file())


@main.group('logger')
def logger_group():
    """Select logger config mode."""
    pass


@logger_group.command('list')
def logger_list():
    """Current logger level."""
    commands.logger_list()


@logger_group.command('select')
@click.option('--level', type=click.Choice(['release', 'debug']))
def logger_set(level):
    """Select logger level."""
    if not level:
        echo_help(logger_set)
        return

    commands.logger_reset(level == 'debug')


@logger_group.command('edit')
def logger_edit():
    """Edit logger config file."""
    click.edit(filename=commands.logger_file())


if __name__ == "__main__":
    main()
