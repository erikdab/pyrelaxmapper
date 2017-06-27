# -*- coding: utf-8 -*-
"""Configuration utilities."""
import datetime
import glob
import logging
import os
import shutil
from configparser import ConfigParser

import click

APPLICATION = 'pyrelaxmapper'

logger = logging.getLogger()


def dir_pkg_conf():
    """Package conf dir path."""
    return search_paths()[0]


def dir_pkg_data():
    """Package data dir path."""
    return search_paths()[1]


def dir_app_data():
    """User application data path."""
    return search_paths()[2]


def search_paths():
    """Return search paths for application files."""
    return [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'conf')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
        click.get_app_dir(APPLICATION),
    ]


def conf_merge(paths=search_paths()):
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
    file_paths = last_in_paths('conf.ini', paths)
    parser = ConfigParser()
    parser.read(file_paths)
    return parser


def conf_app_path():
    """User config file path."""
    return ensure_path(dir_app_data(), 'conf.ini')


def cp(source_dir, source_name, target_dir, target_name=None):
    """Copy file from source to directory and ensure paths exist."""
    target_name = target_name if target_name else source_name
    source_path = ensure_path(source_dir, source_name)
    target_path = ensure_path(target_dir, target_name)
    shutil.copyfile(source_path, target_path)


def cp_file(source_dir, source_name, file):
    """Copy file from source to directory and ensure paths exist."""
    source_path = ensure_path(source_dir, source_name)
    shutil.copyfile(source_path, file)


def cp_conf_app_data(source_name, target_name=None):
    """Copy file from package conf dir to app data."""
    cp(dir_pkg_conf(), source_name, dir_app_data(), target_name)


def cp_conf_file(source_name, file):
    """Copy file from package conf dir to app data."""
    cp_file(dir_pkg_conf(), source_name, file)


def cp_data_app_data(source_name, target_name=None):
    """Copy file from package data dir to app data."""
    cp(dir_pkg_data(), source_name, dir_app_data(), target_name)


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
    file_path : str
        Last file found, or empty if none exist
    """
    file_paths = find_in_paths(filename, paths)
    return file_paths[-1] if file_paths else file_paths


def newest(directory, extension=''):
    """Newest file in directory with extension."""
    pattern = os.path.join(directory, '*{}'.format(extension))
    return max(glob.iglob(pattern), key=os.path.getctime)


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
    file_paths : array_like
        Last file found, or empty if none exist
    """
    file_paths = []
    for path in paths:
        file_path = os.path.join(path, filename)
        if os.path.exists(file_path):
            file_paths.append(file_path)
    return file_paths


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


def ensure_dir(directory):
    """File in directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def ensure_path(directory, filename=''):
    """File in directory."""
    if not isinstance(filename, str):
        filename = str(filename)
    if not filename:
        return ensure_dir(directory)
    output = os.path.join(os.path.expanduser(directory), os.path.dirname(filename))
    if not os.path.exists(output):
        os.makedirs(output)
    return os.path.abspath(os.path.join(output, os.path.basename(filename)))


def ensure_ext(filename, extension=''):
    """Ensure extension is present at end of filename."""
    return filename if extension in filename else '{}{}'.format(filename, extension)


def add_timestamp(filename):
    """Add timestamp to filename."""
    now = datetime.datetime.now()
    return '{} {}'.format(now.strftime('%Y-%m-%d %H:%M'), filename)


def load_properties(file):
    """Prepares .properties file to be opened by ConfigParser.

    Adds a dummy section name so the parser can open it: '[properties]'

    Parameters
    ----------
    file
        File handler with source .properties file.

    Returns
    -------
    fileutils
        File handler ready to be read into a ConfigParser.
    """
    config = file.StringIO()
    config.write('[properties]\n')
    config.write(file.read())
    config.seek(0, os.SEEK_SET)
    return config
