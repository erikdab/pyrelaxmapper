# -*- coding: utf-8 -*-

"""Project cli interface."""

import os
import click
from . import data, __version__


@click.group()
@click.version_option(version=__version__)
def main():
    pass


@main.command()
def make_dict(output):
    """Create a cascading dictionary."""
    # Click parameters
    directory = os.path.join(os.getcwd(), 'dicts')
    output = os.path.join(os.getcwd(), 'dicts.txt')

    click.echo("Generating dict (this can take a long time):")
    lang_dict = data.cascade_dicts(directory)
    click.echo("Results:")
    with open(output, 'w') as file:
        for key, terms in lang_dict:
            tokens = terms[:]
            tokens.expand(key)
            file.write(' '.join(tokens))


if __name__ == "__main__":
    main()
