# -*- coding: utf-8 -*-
"""Main Application commands."""
import os

import click

from pyrelaxmapper import conf, relax


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
