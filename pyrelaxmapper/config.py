# -*- coding: utf-8 -*-
"""Configuration utilities."""
import io
import logging
import os
import re
from configparser import ConfigParser

import click

from pyrelaxmapper.plwn.plwn import PLWordNet
from pyrelaxmapper.pwn.pwn import PWordNet
from pyrelaxmapper import utils

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
    return file_in_dir(CONF['path']['output'], filename)


def cache(filename):
    """Get absolute filename of new data file."""
    return file_in_dir(CONF['path']['output'], os.path.join('cache', filename))


def data(filename):
    """Get absolute filename of new data file."""
    return file_in_dir(CONF['path']['data'], filename)


def make_session(db_name=None):
    """Make DB session."""
    if not db_name:
        db_name = CONF['path']['db-default']
    with open(os.path.expanduser(db_name)) as file:
        settings = load_conf_db(file)
    engine = utils.create_engine(settings)
    return utils.session_start(engine)


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


class Config:
    """Relaxation Labeling Configuration.

    * Source, Target
    * Translator
    * Clean function
    * Keep only caches needed for model selection.
    * Keep caches only in temporary folder (dropped on system reboot)
    * Inserter (inserts mapping results somewhere)
    * POS
    * empties (empty synsets?)
    * include monosemous?
    * graph directory
    * Constraints, constraint weights
    * Should be possible to change most settings here, instead of creating a Python file.
    # Params:
    # Config, Clean cache? ENV vars
    # Clean intermediary caches? (Only keep caches necessary for model selection?)
    """

    # Types of WordNets
    WORDNETS = [PLWordNet, PWordNet]

    def __init__(self, parser=None, source_wn=None, target_wn=None):
        self._constraints = ['ii']
        self._constr_weights = [0]
        self._pos = None
        self._dataset_split = 0.8
        self._wordnets = self.WORDNETS[:]
        self._source_wn = source_wn
        self._target_wn = target_wn
        if parser:
            self.load(parser)

    def add_wn_types(self, wordnets):
        if not isinstance(wordnets, list):
            wordnets = [wordnets]
        full_names = [wordnet.name() for wordnet in Config.WORDNETS]
        for wordnet in wordnets:
            if wordnet.name() in full_names:
                raise ValueError('New wordnets must have unique name()')
            Config.WORDNETS.append(wordnet)

    def load(self, parser):
        """Load configuration from config parser.

        Parameters
        ----------
        parser : configparser.ConfigParser
        """
        if not self._source_wn:
            self._source_wn = self._wnsource_loader(parser, 'source')
        if not self._target_wn:
            self._target_wn = self._wnsource_loader(parser, 'target')
        section = 'main'
        self._pos = parser[section]['pos'] if parser.has_option(section, 'pos') else None
        if parser.has_option(section, 'constraints'):
            self._constraints = parser[section]['constraints']
        section = 'constraints'
        for constraint in self._constraints:
            if parser.has_option(section, constraint):
                self._constr_weights = parser.getint(section, constraint)
            else:
                raise KeyError('Constraint {} in config, but weight missing!'.format(constraint))

    def _wnsource_loader(self, parser, name):
        if 'main' not in parser or name not in parser['main']:
            raise KeyError('WordNet [main][{}] option not in configuration file!'.format(name))
        source_name = parser['main'][name]
        for WordNet in self._wordnets:
            if WordNet.name() == source_name:
                return WordNet(parser['main'][source_name])

    def constraints(self):
        return self._constraints

    def constr_weights(self):
        return self._constr_weights

    def pos(self):
        return self._pos

    def source_wn(self):
        return self._source_wn

    def target_wn(self):
        return self._target_wn

    def cache(self):
        pass


CONF = load_conf()
