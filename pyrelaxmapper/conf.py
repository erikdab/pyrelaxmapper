# -*- coding: utf-8 -*-
import csv
import os
import sys
from collections import defaultdict

from pyrelaxmapper import translate, utils
from pyrelaxmapper.constraints.hh import HHConstraint
from pyrelaxmapper.dirmanager import DirManager
from pyrelaxmapper.utils import clean
from pyrelaxmapper.constrainer import Constrainer
from pyrelaxmapper.plwn.plwn import PLWordNet
from pyrelaxmapper.pwn.pwn import PWordNet
from pyrelaxmapper.wordnet import WordNet


class Config:
    """Application Configuration.

    Parameters
    ----------
    parser : configparser.ConfigParser
        Parser with configuration.
    wn_classes
        WordNets to add to be loadable from configuration parser.
    constrainer
        Constrainer contains constraints for relaxation labeling.
    """
    WORDNETS = [PLWordNet, PWordNet]
    CONSTRAINTS = [HHConstraint]

    ###################################################################
    # Initialization

    def __init__(self, parser, wn_classes=None, constraint_types=None):
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
        self._init_dicts()

        self.cleaner = utils.clean
        self._ctypes = self.CONSTRAINTS[:]
        if constraint_types:
            self._ctypes.extend(constraint_types)
        self.constrainer = None
        self._init_constraints()

        self._candidates = None
        self._translater = None
        self._manual = {}
        self._manual_missing = {}

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
        data_dir, results_dir, cache_dir = parse_dirs(self._parser, 'dirs', dirs)
        context = self.str_wordnets()
        self.data = DirManager(data_dir, context)
        self.results = DirManager(results_dir, context)
        self.cache = DirManager(cache_dir, context)

    def _init_dicts(self):
        """Initialize Dictionaries from args or configuration."""
        self._dicts_dir = self._parser['dirs'].get('dicts', [])
        if self._dicts_dir:
            self._dicts_dir = [os.path.expanduser(dict_)
                               for dict_ in self._parser['dirs'].get('dicts', []).split(',')]
        self.cleaner = clean

    def _init_constraints(self):
        """Initialize constraints from args or configuration."""
        self.constrainer = Constrainer()
        constraints = parse_constraints(self._parser, 'relaxer', self._ctypes)
        self.add_constraints(constraints)

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
                self.cache, self.pos, self.constrainer, self.cleaner, self._dicts_dir)

    def __setstate__(self, state):
        (self._parser, self._wn_classes, self._source_wn, self._target_wn, self.data, self.results,
         self.cache, self.pos, self.constrainer, self.cleaner, self._dicts_dir) = state
        self._manual = None
        self._manual_missing = None
        self._translater = None
        self._dicts = None

    ###################################################################
    # Others

    def str_wordnets(self):
        """Mapping name for folder organization."""
        return '{} -> {}'.format(self._source_wn.name(), self._target_wn.name())

    def str_langs(self):
        """Mapping name for folder organization."""
        return '{} -> {}'.format(self._source_wn.lang(), self._target_wn.lang())

    def add_constraints(self, constraints):
        """Parse and add constraints.

        Returns
        -------
        cnames : list of str
        cweights : dict
        """
        self.constrainer.constraints.extend(constraints)

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

    ###################################################################
    # WordNets

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

    ###################################################################
    # Dictionaries

    def dicts(self):
        """Dictionaries between source and target languages."""
        # self._translater = Translater(dicts, self.cleaner)
        if self._dicts:
            return self._dicts

        self._dicts = {}
        for path in self._dicts_dir:
            name = os.path.basename(path)
            name = name[:name.rfind('.')].title()
            self._dicts.update(self.cache.rw_lazy(name, self._load_dict, [path],
                                                  group=self.str_langs()))
        return self._dicts

    def _load_dict(self, filename):
        """Load dictionary between languages."""
        dict_ = defaultdict(set)
        try:
            with open(filename, 'r') as file:
                reader = csv.reader(file, delimiter=' ')
                for row in reader:
                    dict_[self.cleaner(row[0])].add(self.cleaner(row[1]))
        except FileNotFoundError as e:
            print('Dicts file not found. EXITING.')
            sys.exit(1)
        return dict_

    ###################################################################
    # Candidates

    def candidates(self):
        """Candidates between source and target wordnet."""
        if self._candidates:
            return self._candidates

        self._candidates = self.translater().candidates
        return self._candidates

    def translater(self):
        """Candidates between source and target wordnet."""
        if self._translater:
            return self._translater

        cachename = 'Translater'
        if not self.cache.exists(cachename, True):
            # Merge into wordnet, simplify
            source_lemmas = self.cache.rw_lazy('lemma -> synsets', self.source_wn().lemma_synsets,
                                               [self.cleaner], group=self.source_wn().name())
            target_lemmas = self.cache.rw_lazy('lemma -> synsets', self.target_wn().lemma_synsets,
                                               [self.cleaner], group=self.target_wn().name())
            dicts = self.dicts()
            translater = translate.Translater(self.cleaner, dicts)
            args = [source_lemmas, target_lemmas]
            self._translater = self.cache.rw_lazy(cachename, translater.translate, args, True)
        else:
            self._translater = self.cache.r(cachename, True)
        return self._translater

    ###################################################################
    # Manual mappings

    # Consider combining manual and load manual
    def manual(self):
        """Manual (done) mappings between source and target wordnet."""
        if self._manual:
            return self._manual

        self._manual, self._manual_missing = \
            self.cache.rw_lazy('Manual', self.source_wn().mappings, [self.target_wn()], True)

        return self._manual

    def manual_missing(self):
        """Manual (done) mappings not found in target wordnet.

        Possible reasons:
          - difference in wordnets versions
          - manual mapping introduced new synsets absent in target wn.
        """
        if self._manual:
            return self._manual

        self.manual()
        return self._manual_missing


def parse_dirs(parser, section, options):
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


def parse_constraints(parser, section, ctypes):
    """Parse and add constraints.

    Returns
    -------
    cnames : list of str
    cweights : dict
    """
    cnames = parser.get(section, 'cnames', fallback='').split(',')
    if not cnames:
        return []

    cweights = defaultdict(lambda: defaultdict(float))
    for key, value in parser.items('weights'):
        ctype, ckey = key.split('_')
        cweights[ctype][ckey] = float(value)

    constraints = []
    for ctype in ctypes:
        cnames_ = ctype.cnames_all()
        match = cnames_.intersection(cnames)
        if match:
            cweights_ = cweights.get(ctype.uid(), {})
            constraints.append(ctype(match, cweights_))
    return constraints


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
