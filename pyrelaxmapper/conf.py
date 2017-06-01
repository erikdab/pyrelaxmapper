# -*- coding: utf-8 -*-
"""Configuration utilities."""
from configparser import ConfigParser
import os
import click
import re
import io
import logging

from . import APPLICATION

logger = logging.getLogger()


def search_paths():
    """Returns search paths for program configuration files."""
    return [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'conf')),
            click.get_app_dir(APPLICATION)]


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
    parser = ConfigParser()
    for path in paths:
        conf = os.path.join(path, 'conf.ini')
        if os.path.exists(conf):
            parser.read(conf)
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


def load_dicts(directory):
    """Loads dicts index and creates dict file paths.

    Parameters
    ----------
    directory : string
        Directory containing dictionaries to cascade together.

        Structure:
          index.txt     # Dictionaries names (dir names) to load
          */dict.txt    # Translations for each dictionary

        'index.txt'   format: comma-separated ordered list, example:
            "dicts_dir1,dicts_dir3,dicts_dir2"
        'dict.txt'    format: tab-delimited translations, example:
            "term1\ttranslation1
             term2\ttranslation2"

    Returns
    -------
    tuple
        (list of dict names, list of dict absolute paths)
    """
    filename = os.path.join(directory, 'index.txt')
    if not os.path.exists(filename):
        logger.error('index.txt is missing in path: {0}. '.format(directory))
        return []
    with open(filename, 'r') as file:
        names = file.read().strip().split(',')
        index = [os.path.join(directory, name, 'dict.txt') for name in names]
    return names, index


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
