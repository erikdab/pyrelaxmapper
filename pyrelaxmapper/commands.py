# -*- coding: utf-8 -*-
"""Main Application commands."""
import os

import click

from pyrelaxmapper import data, db, conf, rl
from pyrelaxmapper.plwordnet import queries as plquery, files as plfile


# TODO: Temporary, do this better!
def make_session(db_name='db-default'):
    """Make DB session."""
    parser = conf.load_conf()
    with open(os.path.expanduser(parser['path'][db_name])) as file:
        settings = conf.load_conf_db(file)
    engine = db.create_engine(settings)
    return db.session_start(engine)


def db_info():
    """List DB and external datasets info."""
    limit = 5

    click.secho('Listing file-based dataset summaries:', fg='blue')
    with open(conf.last_in_paths('domains.txt')) as file:
        domains = plfile.load_domains(file)
    click.echo('Domains ({} out of {} total):'.format(limit, len(domains)))
    click.echo('\n'.join(['\t'.join(domain) for domain in domains[0:limit]]))

    with open(conf.last_in_paths('pos.txt')) as file:
        pos = plfile.load_pos(file)
    click.echo('POS ({} out of {} total):'.format(limit, len(pos)))
    click.echo('\n'.join(['\t'.join(pos_) for pos_ in pos[0:limit]]))

    click.secho('Listing plWordNet DB summaries:')
    session = make_session()
    version = plquery.version(session)
    click.echo('plWN version: {}'.format(version))
    pwn_mappings = plquery.pwn_mappings(session)
    click.secho('Preexisting plWN-PWN Mappings ({} out of {}):'
                .format(limit, pwn_mappings.count()), fg='blue')
    pwn_mappings = pwn_mappings.limit(limit).all()
    click.echo('\n'.join(str(mapping) for mapping in pwn_mappings))


def list_config():
    """List application configuration."""
    click.secho(conf.search_paths.__doc__, fg='blue')
    for path in conf.search_paths():
        click.echo(''.join([path, ': (exists)' if os.path.exists(path) else '']))

    click.secho(conf.load_conf.__doc__.splitlines()[0], fg='blue')
    parser = conf.load_conf()
    for section in parser.sections():
        click.echo(section)
        for key in parser[section].keys():
            value = parser[section][key]
            exists = ''
            if section == 'path' and os.path.exists(os.path.expanduser(value)):
                exists = ': (exists)'
            click.echo(''.join(['\t', key, ': ', value, exists]))


def make_dicts():
    """Create cascading dictionary from multiple dicts."""
    parser = conf.load_conf()
    names, index = conf.load_dicts(os.path.expanduser(parser['path']['dicts']))
    if not index:
        exit(1)
    click.secho("Generating dict. Sources:", fg='blue')
    click.echo(str(names))
    lang_dict = data.cascade_dicts(conf.yield_lines(index))

    filename = conf.results('translations.txt')
    with open(filename, 'w') as file:
        file.write('\n'.join(key+' '+' '.join(terms) for key, terms in lang_dict.items()))
    click.secho('Done. Results stored in: {}'.format(filename), fg='blue')


def make_extract():
    """Extract needed data from plWordNet DB."""
    session = make_session()
    click.secho('Extracting units, synsets, hiper and hiponyms from DB.', fg='blue')
    data.db_extract(session)
    click.secho('Done.', fg='blue')


def make_clean():
    """Clean ONLY mapping results."""
    files = ['pierwsi', 'pierwsi2', 'pozostali', 'pozostali2', 'pozostali3']
    for file in files:
        path = conf.results(file+'.txt')
        if os.path.exists(path):
            os.remove(path)

    click.secho('Cleaned mapping results.', fg='blue')


def make_mono():
    """Create monosemous mappings between plWN and PWN."""
    click.secho('Running monosemous mapping.', fg='blue')
    rl.one()
    click.secho('Done monosemous mapping.', fg='blue')


def make_poly():
    """Create polysemous mappings between plWN and PWN."""
    click.secho('Running polysemous mapping.', fg='blue')
    rl.test()
    click.secho('Done polysemous mapping.', fg='blue')