# -*- coding: utf-8 -*-

"""Project cli interface."""

import os
import click
from . import __version__
from . import conf
from . import data
from . import db


@click.group()
@click.version_option(version=__version__)
def main():
    """Application entry point."""
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


@main.command()
def dbms():
    """DB Test function."""
    parser = conf.load_conf()
    with open(os.path.expanduser(parser['db']['default'])) as file:
        settings = conf.load_conf_db(file)
    engine = db.connect(settings)
    version = db.plwn_version(engine)
    click.echo('plWN version: {}'.format(version))


@main.command()
def config():
    """List program configuration."""
    click.secho(conf.search_paths.__doc__, fg='blue')
    for path in conf.search_paths():
        click.echo(''.join([path, ': ', 'exists' if os.path.exists(path) else 'does not exist']))

    click.secho(conf.load_conf.__doc__.splitlines()[0], fg='blue')
    parser = conf.load_conf()
    for section in parser.sections():
        click.echo(section)
        for key in parser[section].keys():
            click.echo(''.join(['\t', key, ':', parser[section][key]]))


if __name__ == "__main__":
    main()
