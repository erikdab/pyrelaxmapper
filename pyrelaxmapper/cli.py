# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from . import pyrelaxmapper
from . import __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for lexical net mapping."""
    pass


@main.group()
def make():
    """Make target action."""
    pass


@make.command('all')
def make_all():
    """Make all targets."""
    pyrelaxmapper.make_dicts()


@make.command('dicts')
def make_dicts():
    """Make a cascading dictionary."""
    pyrelaxmapper.make_dicts()


@main.command()
def db():
    """List database information."""
    pyrelaxmapper.db_version()


@main.command()
def config():
    """List configuration information."""
    pyrelaxmapper.list_config()


if __name__ == "__main__":
    main()
