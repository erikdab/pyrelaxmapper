# -*- coding: utf-8 -*-
"""Application cli interface."""
import click

from pyrelaxmapper import __version__, commands


@click.group()
@click.version_option(version=__version__)
def main():
    """pyrelaxmapper uses relaxation labeling for wordnet mapping."""
    pass


@main.group(chain=True)
def make():
    """Make target action."""


@make.command('extract')
def make_extract():
    """Extract data from plWordNet DB."""
    commands.make_extract()


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
