# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from pyrelaxmapper import __version__, commands, conf


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


# TODO: allow make to show help if no action is passed.
@main.command()
@click.argument('actions', nargs=-1, required=False)
@click.option('--cache/--no-cache', default=True, help='Use caches.')
# ENV FILE
@click.option('--configf', '-c', help='Specify configuration file.')
def make(actions, cache, configf):
    """Make target ACTIONS in correct order. Chainable.

    \b
    ACTIONS:
      all      Make all actions.
      dicts    Make translation dicts.
      extract  Extract plWordNet data from DB.
      map      Perform the mapping actions.
      mono     Map monosemous words (without RL).
      poly     Map polysemous words (with RL)."""
    if not actions:
        return
    parser = conf.load_conf()  # Allow specifying in interface
    config = conf.Config(parser)

    if not cache and any(action in ['mono', 'poly', 'all'] for action in actions):
        commands.make_clean(config)
    if any(action in ['map', 'setup', 'relax', 'all'] for action in actions):
        relaxer = config.cache(config.file_relaxer(), commands.make_setup, [config])
        if all(action not in ['setup'] for action in actions):
            commands.make_relax(relaxer)


@main.command('list config')
def list_config():
    """List configuration information."""
    commands.list_config()


if __name__ == "__main__":
    main()
