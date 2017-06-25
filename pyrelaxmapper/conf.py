# -*- coding: utf-8 -*-
from pyrelaxmapper.dicts import Translater
from pyrelaxmapper.dirmanager import DirManager
from pyrelaxmapper.utils import clean
from pyrelaxmapper.constrainer import Constrainer
from pyrelaxmapper.plwn.plwn import PLWordNet
from pyrelaxmapper.pwn.pwn import PWordNet
from pyrelaxmapper.wordnet import WordNet


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
    translater : pyrelaxmapper.dicts.Translater, optional
        Translater between esp. multi-lingual wordnets.
    """
    WORDNETS = [PLWordNet, PWordNet]

    def __init__(self, parser, wn_classes=None, constrainer=None, translater=None):
        if not parser:
            raise ValueError('Configuration requires a ConfigParser to load.')

        self._parser = parser

        self._wn_classes = self.WORDNETS[:]
        _add_wn_classes(self._wn_classes, wn_classes)
        sections = ['source', 'target']
        self._source_wn, self._target_wn = _select_wordnets(parser, sections, self._wn_classes)
        if not self._target_wn or self._source_wn == self._target_wn:
            self._target_wn = self._source_wn

        dirs = ['data', 'results', 'cache']
        data_dir, results_dir, cache_dir = _parse_dirs(parser, 'dirs', dirs)
        context = self.map_name()
        self.data = DirManager(data_dir, context)
        self.results = DirManager(results_dir, context)
        self.cache = DirManager(cache_dir, context)

        self.pos = parser.get('relaxer', 'pos', fallback='').split(',')

        self.constraints = ['ii']
        self.constr_weights = {'ii': [0, 0, 0]}
        self._constrainer = constrainer

        # if not parser.has_option(section, 'constraints'):
        #     raise KeyError('Relaxation labeling requires at least one constraint!')
        # self._constraints = parser[section]['constraints'].split(',')

        # for constraint in self._constraints:
        #     option = 'weights_{}'.format(constraint)
        # if not parser.has_option(section, option):
        #     raise KeyError('Constraint weight missing: [{}][{}]'.format(constraint, option))
        # self._constr_weights[constraint] = parser[section][option]

        # Incorporate into Translater
        self.cleaner = clean
        self.translater = translater if translater else Translater()

    def __getstate__(self):
        # Save only source and target classes, not the data itself.
        parser = self._parser
        sections = ['source', 'target']
        source_wn, target_wn, = _select_wordnets(parser, sections, self._wn_classes)
        return (self._parser, self._wn_classes, source_wn, target_wn, self.data, self.results,
                self.cache, self.pos, self.constraints, self.constr_weights, self.cleaner,
                self.translater)

    def __setstate__(self, state):
        (self._parser, self._wn_classes, self._source_wn, self._target_wn, self.data, self.results,
         self.cache, self.pos, self.constraints, self.constr_weights, self.cleaner,
         self.translater) = state

    def map_name(self):
        """Mapping name for folder organization."""
        return '{} -> {}'.format(self._source_wn.name(), self._target_wn.name())

    ###################################################################
    # Large data

    def preload(self):
        """Preload large data."""
        self.source_wn()
        self.target_wn()
        self.constrainer()
        # self.translater()

    def loaded(self):
        """Is large data loaded."""
        return self._source_wn.loaded() and self._target_wn.loaded() and self._constrainer

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
        self._target_wn = self.ensure_wn(self._source_wn)
        return self._target_wn

    def constrainer(self):
        """Mapping algorithm constrainer."""
        if not self._constrainer:
            self._constrainer = Constrainer(self.source_wn(), self.target_wn(),
                                            self.constraints, self.constr_weights)
        return self._constrainer
