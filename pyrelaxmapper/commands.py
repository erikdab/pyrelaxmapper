# -*- coding: utf-8 -*-
"""Main Application commands."""
import os
from enum import Enum
import logging

import click
import sys

from pyrelaxmapper import conf, fileutils, utils, relax
from pyrelaxmapper.stats import Stats

logger = logging.getLogger()

# Click Colors
# TODO: turn into enum?
CSuccess = 'green'
CInfo = 'blue'
CError = 'red'
CWarn = 'yellow'


def make_actions(actions, conf_file):
    """Make actions in correct order."""
    # Remove these logs. Now just for test.
    logger.info('Start.')

    config = config_load(conf_file)

    if Action.Clean in actions:
        config_clean(config)

    status = None
    if Action.Relax in actions:
        # could merge
        relaxer = relaxer_load(config)
        status = relaxer_relax(relaxer)

    # Maybe should be able to pass status file as option/input etc.
    if Action.Stats in actions:
        relaxer_stats(status, config)

    logger.info('End.')


#######################################################################
# Relaxer and statistics.

def relaxer_load(config):
    """Load relaxer."""
    click.secho('Loading large data for RL algorithm.', fg=CInfo)
    return relax.Relaxer(config)


def relaxer_relax(relaxer):
    """Run RL Algorithm."""
    click.secho('Running RL algorithm.', fg=CInfo)
    relaxer.relax()
    config = relaxer.config
    stat_mru = fileutils.add_timestamp('Status.pkl')
    click.secho('Writing results.', fg=CInfo)
    config.results.w(stat_mru, relaxer.status, True)
    return relaxer.status


# Create result selector?
def relaxer_stats(status, config):
    """Save statistics for RL Algorithm."""
    result_n = 'stats.csv'
    status_n = 'Status.pkl'

    try:
        stat_mru = fileutils.newest(config.results.dir(True), status_n)
    except ValueError as e:
        click.secho('No results found, run \'make relax\' to generate results.', fg=CWarn)
        sys.exit(1)

    if not status:
        click.secho('Reading most recently saved results.')
        status = config.results.r(stat_mru, True)
    results = '{}{}'.format(stat_mru[:stat_mru.find(status_n)], result_n)

    click.secho('Creating statistics report.', fg=CInfo)
    with open(results, 'w') as file:
        stats = Stats(status)
        stats.create_report(file)


#######################################################################
# Application configuration.

def config_load(conf_file):
    """Load configuration parser and merge with file if present."""
    click.secho('Loading configuration.', fg=CInfo)

    parser = fileutils.conf_merge()
    if conf_file:
        parser.read_file(conf_file)

    return conf.Config(parser)


def config_clean(config):
    """Clean all cache files."""
    click.secho('Cleaning all caches, reloading should take around a minute.', fg=CInfo)
    config.cache.remove_all()


# def configure(config, clean, force_config):
#     if force_config:
#         click.secho('Cleaning configuration cache.', fg=CInfo)
#     if force_config or not config.cache.exists('Config', True):
#         click.secho('Pre-loading data.', fg=CInfo)
#         config.preload()
#         click.secho('Writing configuration cache.', fg=CInfo)
#     return config.cache.rw('Config', config, True, force=force_config)


# To file?
def config_list(conf_file):
    """List application configuration."""
    click.secho('Configuration summary:', color=CInfo)
    click.secho('Search paths:', fg=CInfo)
    for path in fileutils.search_paths():
        path = os.path.join(path, 'conf.ini')
        click.echo(''.join([path, ' <-(exists)' if os.path.exists(path) else '']))

    path = os.environ.get('RLCONF', '')
    if path:
        click.secho('\nRLCONF:', fg=CInfo)
        click.echo(''.join([path, ' <-(exists)' if os.path.exists(path) else '']))

    click.secho('\nMerged configuration:', fg=CInfo)
    default = fileutils.conf_merge([fileutils.dir_pkg_conf()])
    merged = fileutils.conf_merge()
    if conf_file:
        merged.read_file(conf_file)
    sections = list(default.keys())
    for section in sections:
        click.echo(section)
        keys = list(default[section].keys())
        keys.extend(key for key in merged[section].keys() if key not in keys)
        for key in keys:
            v_merged = merged.get(section, key, fallback='')
            v_default = default.get(section, key, fallback='')
            diff = ' '
            if v_merged and not v_default:
                diff = '+'
            elif not v_merged and v_default:
                diff = '-'
            elif v_merged != v_default:
                diff = '~'
            diff += ' '
            value = os.path.expanduser(v_merged)
            exists = ' <-(exists)' if os.path.exists(value) else ''
            click.echo(''.join(['\t', diff, key, ' = ', value, exists]))


def config_exists():
    """Does user config file exist?"""
    return os.path.exists(fileutils.conf_app_path())


def config_remove(conf_file):
    """Reset app config."""
    conf_file.write('')


# Edit writes by default if not exists.

# Removes
def config_reset(conf_file):
    """Reset app config."""
    path = fileutils.ensure_path(fileutils.dir_pkg_conf(), 'conf.ini')
    with open(path) as file:
        conf_file.write(file.read())
    # fileutils.cp_conf_app_data(conf_file)
    click.secho('Config reset to defaults.', fg=CInfo)


def config_erase(conf_file):
    """Erase config."""
    if os.path.exists(fileutils.conf_app_path()):
        conf_file.write('')


def config_file():
    """Path to app config file."""
    return fileutils.conf_app_path()


#######################################################################
# Logger configuration.

def logger_list(debug=True):
    """List logger config information."""
    level = ''
    with open(logger_file(), 'r') as file:
        for line in file:
            if 'level=' in line:
                level = line[line.find('=') + 1:-1]
                break
    color = CWarn if level == 'ERROR' else CWarn
    click.secho('Logger level: {}'.format(level), fg=color)


def logger_reset(debug=True):
    """Set logger configuration."""
    ending = '-debug' if debug else ''
    name = 'DEBUG' if debug else 'RELEASE'
    color = CWarn if debug else CInfo

    click.secho('Logger mode set to {}'.format(name), fg=color)

    fileutils.cp_conf_app_data('logging{}.ini'.format(ending), 'logging.ini')


def logger_file():
    """Path to app config file."""
    return os.path.join(fileutils.conf_app_path(), 'logging.ini')


def logger_edit():
    """Edit logger config file."""
    click.edit(filename=fileutils.in_lowest_path('logging.ini'))


#######################################################################
# Other interface utilities.


class Action(Enum):
    """Application actions."""
    Clean = 'clean'
    Relax = 'relax'
    Stats = 'stats'


def parse_actions(actions):
    """Parse Actions.

    Parameters
    ----------
    actions : list of Action

    Returns
    -------
    set of Action
    """
    return set(utils.enum_factory(Action, set(actions)))
