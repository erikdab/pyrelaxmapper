# -*- coding: utf-8 -*-

"""Configuration utilies."""
from configparser import ConfigParser
import os
import click


APPNAME = 'pyrelaxmapper'


def search_paths():
    """Search paths for program configuration files."""
    return [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'conf')),
            click.get_app_dir(APPNAME)]


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
