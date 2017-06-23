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


def make_clean(config):
    """Cleans all files under the cache directory.

    Parameters
    ----------
    config : conf.Config
    """
    config.clean_cache()


def make_setup(config):
    """Setup relaxation labeling wordnet mapping problem.

    Parameters
    ----------
    config : conf.Config

    Returns
    -------
    pyrelaxmapper.relax.Relaxer
    """
    click.secho('Running relaxation labeling setup.', fg='blue')
    relaxer = relax.Relaxer(config)
    click.secho('Done setting up relaxation labeling.', fg='blue')
    return relaxer


def make_relax(relaxer):
    """Perform relaxation labeling wordnet mapping algorithm.

    Parameters
    ----------
    relaxer : pyrelaxmapper.relax.Relaxer

    Returns
    -------
    relaxer : pyrelaxmapper.relax.Relaxer
    """
    click.secho('Running relaxation labeling.', fg='blue')
    relaxer.relax()
    click.secho('Done relaxation labeling.', fg='blue')
    return relaxer
