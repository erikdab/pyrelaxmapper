# -*- coding: utf-8 -*-
"""Main Application commands."""
import os
from configparser import ConfigParser
from enum import Enum
import logging

import click
import sys

from pyrelaxmapper.constraints.hh import HHConstraint
from pyrelaxmapper import conf, fileutils, utils, relax
from pyrelaxmapper.stats import Stats
from pyrelaxmapper.wordnet import WordNet

logger = logging.getLogger()

# Click Cli Colors
CSuccess = 'green'
CInfo = 'blue'
CError = 'red'
CWarn = 'yellow'


def make_actions(actions, conf_file):
    """Make actions in correct order."""
    config = config_load(conf_file)

    if Action.Clean in actions:
        config_clean(config)

    status = None
    if Action.Relax in actions:
        status = relaxer_relax(config)

    if Action.Stats in actions:
        relaxer_stats(status, config)


#######################################################################
# Relaxer and statistics.

def relaxer_relax(config):
    """Load and Run RL Algorithm."""
    click.secho('Loading large data for RL algorithm.', fg=CInfo)
    relaxer = relax.Relaxer(config)

    click.secho('Running RL algorithm.', fg=CInfo)
    relaxer.relax()
    config = relaxer.config
    stat_mru = fileutils.add_timestamp('Status.pkl')
    click.secho('Writing results.', fg=CInfo)
    config.results.w(stat_mru, relaxer.status, True)
    return relaxer.status


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

    if conf_file:
        parser = ConfigParser()
        parser.read_file(conf_file)
    else:
        parser = fileutils.conf_merge()

    return conf.Config(parser)


def config_clean(config):
    """Clean all cache files."""
    click.secho('Cleaning all caches, next load will take up to a minute.', fg=CInfo)
    config.cache.remove_all()


def diff_char(left, right):
    """Return a character representing the diff between the values."""
    diff = ' '
    if left and not right:
        diff = '+'
    elif not left and right:
        diff = '-'
    elif left != right:
        diff = '~'
    diff += ' '
    return diff


def config_list(conf_file):
    """List application configuration."""
    click.secho('Configuration summary:', color=CInfo)
    click.secho('Search paths:', fg=CInfo)

    active_path = conf_file.name
    rlconf = os.environ.get('RLCONF', '')

    paths = [fileutils.dir_pkg_conf(), fileutils.dir_app_data()]
    paths = [os.path.join(path, 'conf.ini') for path in paths]
    if active_path not in paths:
        paths.append(active_path)
    for path in paths:
        opt = 'option: ' if len(paths) == 3 and path == paths[2] else ''
        env = '$RLCONF: ' if path == rlconf else opt
        exists = ' <-(exists)' if os.path.exists(path) else ''
        active = ' and active' if path == active_path else ''
        click.echo(''.join([env, path, exists, active]))

    click.secho('\nConfiguration listing (diff to defaults):', fg=CInfo)
    default = fileutils.conf_merge([fileutils.dir_pkg_conf()])
    live = fileutils.conf_merge()
    if conf_file:
        live.read_file(conf_file)
    sections = list(live.keys())
    sections.extend(default.keys())
    for section in sections:
        diff_section = diff_char(live.has_section(section), default.has_section(section))
        click.echo('{}{}'.format(diff_section, section))
        keys = []
        if live.has_section(section):
            keys.extend(live[section].keys())
        if default.has_section(section):
            keys.extend(key for key in default[section].keys() if key not in keys)
        for key in keys:
            value = v_live = live.get(section, key, fallback='')
            v_default = default.get(section, key, fallback='')
            diff_value = diff_char(v_live, v_default)

            value = os.path.expanduser(value)
            exists = ' <-(exists)' if os.path.exists(value) else ''
            click.echo('\t{}{} = {}{}'.format(diff_value, key, value, exists))


def config_reset(conf_file):
    """Reset app config."""
    path = fileutils.ensure_path(fileutils.dir_pkg_conf(), 'conf.ini')
    with open(path) as file:
        conf_file.write(file.read())
    click.secho('Config reset to defaults.', fg=CInfo)


def config_file():
    """Path to app config file."""
    path = fileutils.conf_app_path()
    if not os.path.exists(path):
        fileutils.cp_conf_app_data('conf.ini', 'conf.ini')
    return path


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

    # Can throw permission error.
    fileutils.cp_conf_app_data('logging{}.ini'.format(ending), 'logging.ini')


def logger_file():
    """Path to app config file."""
    return fileutils.last_in_paths('logging.ini')


def logger_edit():
    """Edit logger config file."""
    click.edit(filename=fileutils.last_in_paths('logging.ini'))


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


def usage_example():
    """A short usage example for all algorithm tasks."""
    class TestWordNet(WordNet):
        """Test wordnet implementation."""
        pass
    # Load the config parser from a file, stdin, or any other location.
    parser = fileutils.conf_merge()
    # Define non-builtin wordnet implementations if using them.
    wn_cls = [TestWordNet]
    # Define non-builtin constraints if using them.
    constraint_cls = [HHConstraint]
    # Initialize the configuration manager.
    config = conf.Config(parser, wn_cls, constraint_cls)
    # Initialize the relaxation labeling algorithm.
    relaxer = relax.Relaxer(config)
    # Run the relaxation labeling algorithm.
    relaxer.relax()
    # Save statistics to file.
    stats = Stats(relaxer.status)
    with open(config.results.path('results.csv', True), 'w') as file:
        stats.create_report(file)
