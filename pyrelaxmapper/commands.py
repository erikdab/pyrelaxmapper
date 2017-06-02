# -*- coding: utf-8 -*-
"""Main Application commands."""
import os

import click

from pyrelaxmapper import data, db, conf
from pyrelaxmapper.plwordnet import queries as plquery
from pyrelaxmapper.plwordnet import files as plfile


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


def db_info():
    """List DB and external datasets info."""
    parser = conf.load_conf()
    with open(os.path.expanduser(parser['path']['db-default'])) as file:
        settings = conf.load_conf_db(file)
    engine = db.create_engine(settings)
    session = db.session_start(engine)
    version = plquery.version(session)
    click.echo('plWN version: {}'.format(version))

    click.secho('Listing file-based dataset summaries:', fg='blue')
    with open(conf.search_in_paths('domains.txt')[-1]) as file:
        domains = plfile.load_domains(file)
    click.echo('Domains (5 out of {} total):'.format(len(domains)))
    click.echo('\n'.join(['\t'.join(domain) for domain in domains[0:5]]))

    with open(conf.search_in_paths('pos.txt')[-1]) as file:
        pos = plfile.load_pos(file)
    click.echo('POS (5 out of {} total):'.format(len(pos)))
    click.echo('\n'.join(['\t'.join(pos_) for pos_ in pos[0:5]]))


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
