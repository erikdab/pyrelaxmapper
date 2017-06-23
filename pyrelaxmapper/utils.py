# -*- coding: utf-8 -*-
import io
import os
import logging
import re
from configparser import ConfigParser

import numpy as np
import sqlalchemy
import sqlalchemy.engine.url
import sqlalchemy.orm

logger = logging.getLogger()


def clean(term, spaces=False):
    """Clean symbols for term."""
    rep = {'(': '', ')': '', 'the ': '', '/': '', ' ': '_', '-': '_', ',': ''}
    # if spaces:
    #     rep[' '] = '_'
    return multi_replace(term.strip().lower(), rep).strip()


def multi_replace(text, replacements, ignore_case=False):
    """
    Given a string and a dict, replaces occurrences of the dict keys found in the
    string, with their corresponding values. The replacements will occur in "one pass",
    i.e. there should be no clashes.

    Parameters
    ----------
    text : str
        string to perform replacements on
    replacements : dict
        replacement dictionary {str_to_find: str_to_replace_with}
    ignore_case : bool
        whether to ignore case when looking for matches

    Returns
    -------
    str
        str the replaced string
    """
    # Sort by length so that the shorter strings don't replace the longer ones.
    rep_sorted = sorted(replacements, key=lambda s: len(s[0]), reverse=True)

    rep_escaped = [re.escape(replacement) for replacement in rep_sorted]

    pattern = re.compile("|".join(rep_escaped), re.I if ignore_case else 0)

    return pattern.sub(lambda match: replacements[match.group(0)], text)


#######################################################################
# Functions

def normalized(a, axis=-1, order=2):
    """Normalize numpy vector to 1

    Parameters
    ----------
    a : np.ndarray
    axis : int
    order : int

    Returns
    -------
    np.ndarray
    """
    l2 = np.atleast_1d(np.linalg.norm(a, order, axis))
    l2[l2 == 0] = 1
    return a / np.expand_dims(l2, axis)


#######################################################################
# Database utilities.


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


def make_session(filename):
    """Make DB session."""
    with open(filename) as file:
        settings = load_conf_db(file)
    engine = create_engine(settings)
    return session_start(engine)


def create_engine(settings):
    """Create an UTF-8 SQLAlchemy engine from settings dict."""
    if 'mysql' in settings['drivername']:
        settings['query'] = {'charset': 'utf8mb4'}
    url = sqlalchemy.engine.url.URL(**settings)
    engine = sqlalchemy.create_engine(url, echo=False)
    return engine


def session_start(engine):
    """Start an SQLAlchemy session."""
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    return Session()
