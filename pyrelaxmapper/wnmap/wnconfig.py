# -*- coding: utf-8 -*-
"""Relaxation labeling Configuration."""
from plwordnet.plsource import PLWordNet
from pwn.psource import PWordNet


class WNConfig:
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
        full_names = [wordnet.name() for wordnet in WNConfig.WORDNETS]
        for wordnet in wordnets:
            if wordnet.name() in full_names:
                raise ValueError('New wordnets must have unique name()')
            WNConfig.WORDNETS.append(wordnet)

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
