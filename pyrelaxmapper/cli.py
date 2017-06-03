# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from pyrelaxmapper import __version__, commands


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


# TODO: Document possible arguments
@main.group()
@click.argument('actions', nargs=-1)
def make(actions):
    """Make target ACTIONS in correct order. Chainable.

    \b
    ACTIONS:
      all      Make all actions.
      dicts    Make translation dicts.
      extract  Extract plWordNet data from DB.
      one      Run step one of algorithm."""
    if any(action in ['dicts', 'all'] for action in actions):
        commands.make_dicts()
    if any(action in ['extract', 'all'] for action in actions):
        commands.make_extract()
    if any(action in ['one', 'all'] for action in actions):
        commands.make_one()


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
