# -*- coding: utf-8 -*-
import csv
import os
from collections import defaultdict

from pyrelaxmapper.constraints.hh import HHConstraint
from pyrelaxmapper.dirmanager import DirManager
from pyrelaxmapper.utils import clean
from pyrelaxmapper.constrainer import Constrainer
from pyrelaxmapper.plwn.plwn import PLWordNet
from pyrelaxmapper.pwn.pwn import PWordNet
from pyrelaxmapper.wordnet import WordNet


# TODO: ENVVAR
# TODO: Improve validation
class Config:
    """Application Configuration.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parser with configuration.
    wn_classes : list of pyrelaxmapper.wordnet.WordNet
        WordNets to add to be loadable from configuration parser.
    constrainer : pyrelaxmapper.constrainer.Constrainer, optional
        Constrainer contains constraints for relaxation labeling.
    dicts : pyrelaxmapper.dicts.Translater, optional
        Translater between esp. multi-lingual wordnets.
    """
    WORDNETS = [PLWordNet, PWordNet]
    CONSTRAINTS = [HHConstraint]

    ###################################################################
    # Initialization

    def __init__(self, parser, wn_classes=None, constrainer=None, dicts=None):
        if not parser:
            raise ValueError('Configuration requires a ConfigParser to load.')

        self._parser = parser

        self._wn_classes = None
        self._source_wn = None
        self._target_wn = None
        self._init_wordnets(wn_classes)

        self.data = None
        self.results = None
        self.cache = None
        self._init_datadirs()

        self._dicts_dir = None
        self._dicts = None
        self._init_dicts(dicts)

        self.cleaner = None
        self._ctypes = None
        self.constrainer = None
        self._init_constraints(constrainer)

        # Others
        self.pos = parser.get('relaxer', 'pos', fallback='').split(',')

    def _init_wordnets(self, wn_classes):
        """Initialize WordNet classes from args or configuration.

        Does not preload wordnets.
        """
        self._wn_classes = self.WORDNETS[:]
        _add_wn_classes(self._wn_classes, wn_classes)
        self._source_wn, self._target_wn = self._parse_wn_classes()

    def _init_datadirs(self):
        """Initialize data directories from configuration."""
        dirs = ['data', 'results', 'cache']
        data_dir, results_dir, cache_dir = _parse_dirs(self._parser, 'dirs', dirs)
        context = self.map_name()
        self.data = DirManager(data_dir, context)
        self.results = DirManager(results_dir, context)
        self.cache = DirManager(cache_dir, context)

    def _init_dicts(self, dicts):
        """Initialize Dictionaries from args or configuration."""
        self._dicts_dir = self._parser['dirs'].get('dicts', [])
        if self._dicts_dir:
            self._dicts_dir = [os.path.expanduser(dict_)
                               for dict_ in self._parser['dirs'].get('dicts', []).split(',')]
        self.cleaner = clean
        self._dicts = dicts

    def _init_constraints(self, constrainer):
        """Initialize constraints from args or configuration."""
        section = 'relaxer'
        self._ctypes = self.CONSTRAINTS[:]
        cnames = self._parser.get(section, 'cnames', fallback='').split(',')
        if not cnames:
            raise KeyError('Relaxation labeling requires at least one constraint!')

        cweights = defaultdict(lambda: defaultdict(float))
        for key, value in self._parser.items('weights'):
            ctype, ckey = key.split('_')
            cweights[ctype][ckey] = float(value)

        self.constrainer = constrainer if constrainer else Constrainer()
        self.add_constraints(cnames, cweights)

    def _parse_wn_classes(self):
        """Get WordNet classes for source and target."""
        parser = self._parser
        sections = ['source', 'target']
        source_cls, target_cls, = _select_wordnets(parser, sections, self._wn_classes)
        if not target_cls or source_cls == target_cls:
            target_cls = source_cls
        return source_cls, target_cls

    def __getstate__(self):
        # Save only source and target classes, not the data itself.
        source_cls, target_cls = self._parse_wn_classes()
        return (self._parser, self._wn_classes, source_cls, target_cls, self.data, self.results,
                self.cache, self.pos, self.constrainer, self.cleaner, self._dicts_dir, None)

    def __setstate__(self, state):
        (self._parser, self._wn_classes, self._source_wn, self._target_wn, self.data, self.results,
         self.cache, self.pos, self.constrainer, self.cleaner, self._dicts_dir,
         self._dicts) = state

    ###################################################################
    # Others

    def map_name(self):
        """Mapping name for folder organization."""
        return '{} -> {}'.format(self._source_wn.name(), self._target_wn.name())

    def add_constraints(self, cnames, cweights):
        """Parse and add constraints.

        Returns
        -------
        cnames : list of str
        cweights : dict
        """
        if not cnames:
            return
        for ctype in self._ctypes:
            cnames_ = ctype.cnames_all()
            match = cnames_.intersection(cnames)
            if match:
                cweights_ = cweights.get(ctype.uid(), {})
                self.constrainer.constraints.append(ctype(match, cweights_))

    ###################################################################
    # Large data

    def preload(self):
        """Preload large data."""
        self.source_wn()
        self.target_wn()
        self.dicts()

    def loaded(self):
        """Is large data loaded."""
        return self._source_wn.loaded() and self._target_wn.loaded()

    def ensure_wn(self, wordnet):
        """Ensure wordnet is loaded, cache is saved and return it."""
        if not wordnet.loaded():
            wordnet = self.cache.rw_lazy(wordnet.uid(), wordnet.load, [], group=wordnet.name())
        return wordnet

    def source_wn(self):
        """Mapping source wordnet."""
        self._source_wn = self.ensure_wn(self._source_wn)
        return self._source_wn

    def target_wn(self):
        """Mapping target wordnet."""
        self._target_wn = self.ensure_wn(self._target_wn)
        return self._target_wn

    def dicts(self):
        """Mapping algorithm constrainer."""
        if not self._dicts:
            self._dicts = self._load_dicts()
            # self._translater = Translater(dicts, self.cleaner)
        return self._dicts

    def _load_dicts(self):
        dicts = {}
        for path in self._dicts_dir:
            name = os.path.basename(path)
            name = name[:name.rfind('.')].title()
            dicts.update(self.data.rw_lazy(name, self._load_dict, [path]))
        return dicts

    # TODO: Lower?
    def _load_dict(self, filename):
        dict_ = defaultdict(set)
        with open(filename, 'r') as file:
            reader = csv.reader(file, delimiter=' ')
            for row in reader:
                dict_[self.cleaner(row[0])].add(self.cleaner(row[1]))
        return dict_


def _parse_dirs(parser, section, options):
    """Parse directory configuration option.

    Returns
    ------
    list of str
    """
    dirs = []
    for option in options:
        try:
            dirs.append(parser.get(section, option))
        except KeyError as e:
            raise KeyError('[{}][{}] Required.')
    return dirs


def _add_wn_classes(wn_classes, wordnets):
    """Add WordNet type to permit it to be loaded from a config file."""
    if not wordnets:
        return
    if not isinstance(wordnets, list):
        wordnets = [wordnets]
    full_names = [wordnet.uid() for wordnet in wn_classes]
    for wordnet in wordnets:
        if not issubclass(wordnet, WordNet):
            raise ValueError('New wordnet type {} does not subclass {}'
                             .format(wordnet.__name__, type(WordNet)))
        if wordnet.uid() in full_names:
            raise ValueError('New WordNet type {} does not have unique uid: {}'
                             .format(wordnet.__name__, wordnet.uid()))
        wn_classes.append(wordnet)


def _select_wordnets(parser, sections, wn_classes):
    """Merge WordNet types.

    Parameters
    ----------
    parser
    sections
    wn_classes

    Returns
    -------
    list of pyrelaxmapper.wordnet.WordNet
    """
    wordnets = [None] * len(sections)
    for idx, section in enumerate(sections):
        option = 'uid'
        if not parser.has_option(section, option):
            if section == 'source':
                raise KeyError('WordNet [{}][{}] option not in config file!'
                               .format(section, option))
            else:
                continue
        wordnet_uid = parser[section][option]
        for wordnet in wn_classes:
            if wordnet.uid() == wordnet_uid:
                wordnets[idx] = wordnet(parser, section, False)
    return wordnets
