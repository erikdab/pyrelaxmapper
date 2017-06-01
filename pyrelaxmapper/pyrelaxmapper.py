# -*- coding: utf-8 -*-
"""Application main logic."""
import os

import click

from . import plwordnet
from . import conf
from . import data


def make_dicts():
    """Create cascading dictionary from multiple dicts."""
    parser = conf.load_conf()
    names, index = conf.load_dicts(os.path.expanduser(parser['path']['dicts']))
    if not index:
        exit(1)
    click.secho("Generating dict. Sources:", fg='blue')
    click.echo(str(names))
    lang_dict = data.cascade_dicts(conf.yield_lines(index))

    directory = os.path.expanduser(parser['path']['output'])
    filename = os.path.join(directory, 'dicts.txt')
    if not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w') as file:
        file.write('\n'.join(key+' '+' '.join(terms) for key, terms in lang_dict.items()))
    click.secho("Done. Results stored in: {}".format(filename), fg='blue')


def db_version():
    """Print DB version."""
    parser = conf.load_conf()
    with open(os.path.expanduser(parser['path']['db-default'])) as file:
        settings = conf.load_conf_db(file)
    engine = plwordnet.create_engine(settings)
    version = plwordnet.query_version(engine)
    click.echo('plWN version: {}'.format(version))


def list_config():
    """List application configuration."""
    click.secho(conf.search_paths.__doc__, fg='blue')
    for path in conf.search_paths():
        click.echo(''.join([path, ': ', 'exists' if os.path.exists(path) else 'does not exist']))

    click.secho(conf.load_conf.__doc__.splitlines()[0], fg='blue')
    parser = conf.load_conf()
    for section in parser.sections():
        click.echo(section)
        for key in parser[section].keys():
            click.echo(''.join(['\t', key, ': ', parser[section][key]]))
