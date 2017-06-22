# -*- coding: utf-8 -*-
"""Configuration utilities."""
import io
import logging
import os
import re
from configparser import ConfigParser

import click

from pyrelaxmapper import db

APPLICATION = 'pyrelaxmapper'

logger = logging.getLogger()


# TODO: Some way to extend this? In CONF!
# Split conf and data? conf_paths, data_paths?
def search_paths():
    """Returns search paths for program configuration files."""
    return [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'conf')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
            click.get_app_dir(APPLICATION)]


def file_in_dir(directory, filename):
    """File in directory."""
    output = os.path.join(os.path.expanduser(directory), os.path.dirname(filename))
    if not os.path.exists(output):
        os.makedirs(output)
    return os.path.abspath(os.path.join(output, os.path.basename(filename)))


# TODO: Temporary. Think of something better? :D
def results(filename):
    """Get absolute filename of new data file."""
    return file_in_dir(config['path']['output'], filename)


def cache(filename):
    """Get absolute filename of new data file."""
    return file_in_dir(config['path']['output'], os.path.join('cache', filename))


def data(filename):
    """Get absolute filename of new data file."""
    return file_in_dir(config['path']['data'], filename)


def make_session(db_name=None):
    """Make DB session."""
    if not db_name:
        db_name = config['path']['db-default']
    with open(os.path.expanduser(db_name)) as file:
        settings = load_conf_db(file)
    engine = db.create_engine(settings)
    return db.session_start(engine)


def last_in_paths(filename, paths=search_paths()):
    """Find last file with pattern in paths.

    Parameters
    ----------
    paths : list
        List of paths to search in
    filename : str
        Filename to search for

    Returns
    -------
    file_paths : str
        Last file found, or empty if none exist
    """
    file_paths = find_in_paths(filename, paths)
    return file_paths[-1] if file_paths else file_paths


def find_in_paths(filename, paths=search_paths()):
    """Find last file with pattern in paths.

    Parameters
    ----------
    paths : list
        List of paths to search in
    filename : str
        Filename to search for

    Returns
    -------
    list
        Last file found, or empty if none exist
    """
    file_paths = []
    for path in paths:
        file_path = os.path.join(path, filename)
        if os.path.exists(file_path):
            file_paths.append(file_path)
    return file_paths


def load_conf(paths=search_paths()):
    """Merge multiple configuration files.

    Parameters
    ----------
    paths : list
        Paths in which to search for 'conf.ini' files.

    Returns
    -------
    ConfigParser
        Single config parser with merged settings.
    """
    file_paths = last_in_paths('conf.ini')
    parser = ConfigParser()
    parser.read(file_paths)
    return parser


def load_conf_db(file):
    """Loads database settings from a Java-style properties file.

    Parameters
    ----------
    file
        File handler with database properties in Java .properties file.

    Returns
    -------
    dict
        keys: ['drivername', 'host', 'port', 'database', 'username',
               'password']
    """
    db_parser = ConfigParser()
    db_parser.read_file(load_properties(file))
    conf = db_parser['properties']
    match = re.search('(mysql):\/\/(.+?):?(\d+)?\/(.+)(?=\?)', conf['Url'])
    if len(match.groups()) != 4:
        pattern = '..mysql://host[:port]/database..'
        raise ValueError('Property "Url" in database properties does not match pattern: {}.'
                         .format(pattern))

    keys = ('drivername', 'host', 'port', 'database')
    settings = {key: value for key, value in zip(keys, match.groups())}
    settings['username'] = conf['User']
    settings['password'] = conf['Password']

    return settings


def yield_lines(filenames):
    """Yield all lines from files.

    Logs a debug level message if file does not exist and continues.

    Yields
    ------
    string
        all lines from files
    """
    for filename in filenames:
        if not os.path.exists(filename):
            logger.debug('File {0} does not exist.'.format(filename))
            continue
        with open(filename, 'r') as file:
            for line in file:
                yield line


def load_properties(file):
    """Prepares .properties file to be opened by ConfigParser.

    Adds a dummy section name so the parser can open it: '[properties]'

    Parameters
    ----------
    file
        File handler with source .properties file.

    Returns
    -------
    file
        File handler ready to be read into a ConfigParser.
    """
    config = io.StringIO()
    config.write('[properties]\n')
    config.write(file.read())
    config.seek(0, os.SEEK_SET)
    return config


config = load_conf()
