# -*- coding: utf-8 -*-
"""Application cli interface."""
import os
import shutil
from configparser import ConfigParser

import click

from pyrelaxmapper import __version__, commands, conf, relax


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


@main.command()
@click.argument('actions', nargs=-1, required=False)
@click.option('--clean', default=False, help='Use caches.')
@click.option('--configf', '-c', help='Specify configuration file.')
def make(actions, clean, configf):
    """Make target ACTIONS in correct order. Chainable.

    \b
    ACTIONS:
      all      Make all actions.
      map      Setup and run relaxation labeling.
      setup    Setup relaxation labeling.
      relax    Run relaxation labeling.
      """
    if not actions:
        return

    click.secho('Loading application configuration.', fg='blue')
    parser = ConfigParser(configf) if configf else conf.load_conf()
    config = conf.Config(parser, clean)

    if any(action in ['map', 'setup', 'relax', 'all'] for action in actions):
        click.secho('Loading relaxation labeling setup.', fg='blue')
        relaxer = config.cache('Relaxer', relax.Relaxer, [config], group=config.mapping_group())

        # If not only setup
        if actions != ['setup']:
            click.secho('Running relaxation labeling.', fg='blue')
            relaxer.relax()


@main.command('list-config')
def list_config():
    """List configuration information."""
    commands.list_config()


@main.command('set-logger')
@click.option('--release/--debug', default=True, help='Logger mode.')
def set_logger(release):
    """Copy logger config template to app dir."""
    if release:
        click.secho('Set logger mode to RELEASE', color='red')
    else:
        click.secho('Set logger mode to DEBUG', color='blue')
    logging_conf = 'logging.ini' if release else 'logging-debug.ini'
    shutil.copyfile(os.path.join(conf.dir_pkg_conf(), logging_conf),
                    conf.file_in_dir(conf.dir_app_data(), 'logging.ini'))


if __name__ == "__main__":
    main()
