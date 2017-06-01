# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from pyrelaxmapper import __version__, commands


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


@main.group()
def make():
    """Make target action."""
    pass


@make.command('all')
def make_all():
    """Make all targets."""
    commands.make_dicts()


@make.command('dicts')
def make_dicts():
    """Make a cascading dictionary."""
    commands.make_dicts()


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
