# -*- coding: utf-8 -*-
"""Configuration utilities."""
import io
import logging
import os
import pickle
import shutil
import tempfile
from configparser import ConfigParser

import click

from pyrelaxmapper import utils, dicts
from pyrelaxmapper.constraints import Constrainer
from pyrelaxmapper.plwn.plwn import PLWordNet
from pyrelaxmapper.pwn.pwn import PWordNet
from pyrelaxmapper.wordnet import WordNet

APPLICATION = 'pyrelaxmapper'

logger = logging.getLogger()


#######################################################################
# I/O utilities.


def search_paths():
    """Returns search paths for program configuration files."""
    return [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'conf')),
            os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')),
            click.get_app_dir(APPLICATION)]

  
def ensure_dir(directory):
    """File in directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def ensure_dir(directory):
    """File in directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def file_in_dir(directory, filename):
    """File in directory."""
    output = os.path.join(os.path.expanduser(directory), os.path.dirname(filename))
    if not os.path.exists(output):
        os.makedirs(output)
    return os.path.abspath(os.path.join(output, os.path.basename(filename)))


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


def clean_directory(directory):
    """Remove all files and folders recursively in directory.

    Parameters
    ----------
    directory : str
        Directory to clean.
    """
    shutil.rmtree(directory)
    os.makedirs(directory)


def cached(name, func, args=None, group=None, cache_dir=tempfile.gettempdir()):
    """Load from cache file or create and save to cached file.

    Parameters
    ----------
    name : str
        Name of cache file
    func
        Can be function, or class
    args : list or any
        Args to pass to function / class
    group : str
        cache group (folder)
    cache_dir : str
        Cache directory
    """
    if args is None:
        args = []
    elif not isinstance(args, list):
        args = [args]

    filename = file_in_dir(cache_dir, name if not group else os.path.join(group, name))

    if '.pkl' not in filename:
        filename += '.pkl'

    group_name = '{}/{}'.format(group, name) if group else name
    source = 'from cache' if os.path.exists(filename) else 'live'
    logger.info('Loading "{}" {}.'.format(group_name, source))

    data = None
    if source == 'from cache':
        try:
            data = load_obj(filename)
        except ModuleNotFoundError as e:
            logger.debug('Cache loading error "{}". File: {}.'.format(e, filename))
    if not data:
        data = func(*args)
        save_obj(data, filename)

    # Also: Object generation function may have their own caches!
    # WHY? For time measurement. We know exactly how long it took!
    logger.info('Loaded "{}".'.format(group_name))
    return data


def save_obj(obj, name):
    with open(name, 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)


#######################################################################
# File format loaders


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
    """Application Configuration.

class Config:
    """Application Configuration.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parser with configuration.
    source_wn : pyrelaxmapper.wordnet.WordNet, optional
        WordNet to find mapping for.
    target_wn : pyrelaxmapper.wordnet.WordNet, optional
        WordNet to find mappings in.
    constrainer : pyrelaxmapper.constraints.Constrainer, optional
        Constrainer contains constraints for relaxation labeling.
    translater : pyrelaxmapper.dicts.Translater, optional
        Translater between esp. multi-lingual wordnets.
    """
    # WordNet source builtin types
    WORDNETS = [PLWordNet, PWordNet]

    def __init__(self, parser, source_wn=None, target_wn=None, constrainer=None, translater=None):
        self._pos = None
        self._dataset_split = 0.8

        self._wordnets = self.WORDNETS[:]
        self._source_wn = source_wn
        self._target_wn = target_wn

        self._constraints = ['ii']
        self._constr_weights = {'ii': [0, 0, 0]}
        self._constrainer = constrainer

        self._cleaner = utils.clean
        self._translater = translater if translater else dicts.Translater()

        self._cache = True
        self._cache_dir = ''
        self._data_dir = ''
        self._results_dir = ''

        if parser:
            self.load(parser)

    def add_wn_types(self, wordnets):
        """Add WordNet type to permit it to be loaded from a config file.

        Parameters
        ----------
        wordnets : list of pyrelaxmapper.wordnet.WordNet
        """
        if not isinstance(wordnets, list):
            wordnets = [wordnets]
        full_names = [wordnet.uid() for wordnet in self._wordnets]
        for wordnet in wordnets:
            if not issubclass(wordnet, WordNet):
                raise ValueError('New wordnet type {} does not subclass {}'
                                 .format(wordnet.__name__, type(WordNet)))
            if wordnet.uid() in full_names:
                raise ValueError('New WordNet type {} does not have unique uid: {}'
                                 .format(wordnet.__name__, wordnet.uid()))
            self._wordnets.append(wordnet)

    def load(self, parser):
        """Load configuration from config parser.

        Parameters
        ----------
        parser : configparser.ConfigParser
        """
        section = 'main'
        self._cache = parser.getboolean(section, 'keep_cache', fallback=True)

        section = 'path'
        self._cache_dir, self._data_dir, self._results_dir = \
            self._parse_dirs(parser, section, ['cache', 'data', 'results'])

        section = 'relaxer'
        self._pos = parser.get(section, 'pos', fallback='').split(',')

        if not parser.has_option(section, 'constraints'):
            raise KeyError('Relaxation labeling requires at least one constraint!')
        self._constraints = parser[section]['constraints'].split(',')

        for constraint in self._constraints:
            option = 'weights_{}'.format(constraint)
            if not parser.has_option(section, option):
                raise KeyError('Constraint weight missing: [{}][{}]'.format(constraint, option))
            self._constr_weights[constraint] = parser[section][option]

        if self._source_wn is None:
            self._source_wn = self._wnsource_loader(parser, 'source')
        if self._target_wn is None and parser.has_section('target'):
            self._target_wn = self._wnsource_loader(parser, 'target')
        else:
            self._target_wn = self._source_wn

        if self._constrainer is None:
            self._constrainer = Constrainer(self._source_wn, self._target_wn,
                                            self._constraints, self._constr_weights)

        # logging.config.fileConfig(last_in_paths('logging.ini'))

    def _parse_dirs(self, parser, section, options):
        """Parse directory configuration option.

        Yields
        ------
        str
        """
        for option in options:
            yield os.path.expanduser(parser.get(section, option, fallback=tempfile.gettempdir()))

    def _wnsource_loader(self, parser, name):
        """Load WordNet according to config option, and cache."""
        option = 'uid'
        if not parser.has_option(name, option):
            raise KeyError('WordNet [{}][{}] option not in config file!'.format(name, option))
        wordnet_uid = parser[name][option]
        for wordnet in self._wordnets:
            if wordnet.uid() == wordnet_uid:
                return self.cache(wordnet.uid(), wordnet, [parser, name], group=wordnet.name())

    def constrainer(self):
        return self._constrainer

    def constraints(self):
        return self._constraints

    def cleaner(self):
        return self._cleaner

    def translater(self):
        return self._translater

    def constr_weights(self):
        return self._constr_weights

    def source_wn(self):
        return self._source_wn

    def target_wn(self):
        return self._target_wn

    def pos(self):
        return self._pos

    def cache(self, name, func, args=None, group=None):
        """Cache or load live the result of a callable object.

        Parameters
        ----------
        name : str
            Name of cache file
        func
            Any callable
        args : list
            Args to pass to function / class
        group : str
            cache group (folder)
        """
        return cached(name, func, args, group, self.cache_dir()) if self._cache else func(*args)

    def cache_dir(self):
        return ensure_dir(self._cache_dir)

    def data_dir(self):
        return ensure_dir(self._data_dir)

    def results_dir(self):
        return ensure_dir(self._results_dir)

    def clean_cache(self):
        clean_directory(self.cache_dir())

    def mapping_group(self):
        return '{} -> {}'.format(self.source_wn().name(), self.target_wn().name())
