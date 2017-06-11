# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from pyrelaxmapper import __version__, commands


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


# TODO: allow make to show help if no action is passed.
@main.command()
@click.argument('actions', nargs=-1, required=False)
@click.option('--clean/--no-clean', default=True, help='Clean old mapping output.')
def make(actions, clean):
    """Make target ACTIONS in correct order. Chainable.

    \b
    ACTIONS:
      all      Make all actions.
      dicts    Make translation dicts.
      extract  Extract plWordNet data from DB.
      map      Perform the mapping actions.
      mono     Map monosemous words (without RL).
      poly     Map polysemous words (with RL)."""
    if any(action in ['dicts', 'all'] for action in actions):
        commands.make_dicts()
    if any(action in ['extract', 'all'] for action in actions):
        commands.make_extract()
    if any(action in ['trans', 'all'] for action in actions):
        commands.make_translate()
    if clean and any(action in ['mono', 'poly', 'all'] for action in actions):
        commands.make_clean()
    if any(action in ['map', 'mono', 'all'] for action in actions):
        commands.make_mono()
    if any(action in ['map', 'poly', 'all'] for action in actions):
        commands.make_poly()


@main.command()
def db():
    """List database information."""
    commands.db_info()


@main.command()
def config():
    """List configuration information."""
    commands.list_config()


if __name__ == "__main__":
    main()
