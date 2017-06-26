# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from pyrelaxmapper import __version__, commands
from pyrelaxmapper.commands import Action


#######################################################################
# Click Functions

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


def conf_option(mode='r'):
    """Config file loader using Click option decorator.

    Loads first in order: -c PATH, $RLCONF, app-dir, pkg-conf.

    Parameters
    ----------
    mode : str
        Mode to open File in (r, w, a, rb, wb, ...)
    """
    return click.option('conf_file', '-c', envvar='RLCONF', default=commands.config_file(),
                        type=click.File(mode), help='Configuration file.')


#######################################################################
# Interface Definition.


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


@main.command()
@click.argument('actions', callback=validate_actions, nargs=-1)
@conf_option()
def make(actions, conf_file):
    """Make target ACTIONS in correct order. Chainable.

    \b
    ACTIONS:
      clean    Clean all caches.
      relax    Run RL algorithm and save results.
      stats    Create statistics report.
    """
    if actions:
        return commands.make_actions(actions, conf_file)
    echo_help(make)


#######################################################################
# Configuration Interface.

@main.group('config')
def config_group():
    """Configuration utilities."""
    pass


@config_group.command('list')
@conf_option()
def config_list(conf_file):
    """List merged application configuration."""
    commands.config_list(conf_file)


@config_group.command('reset')
@click.option('--yes', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Are you sure you want to reset config?')
@conf_option('w')
def config_reset(conf_file):
    """Set user config file to defaults."""
    commands.config_reset(conf_file)


@config_group.command('edit')
@conf_option()
def config_edit(conf_file):
    """Edit user config file."""
    click.edit(filename=conf_file.name)


#######################################################################
# Logger Interface.

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
