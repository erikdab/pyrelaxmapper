# -*- coding: utf-8 -*-
import copy

import logging

logger = logging.getLogger()


class Mapping:
    """RL Mapping class between a source and target unit.

    """
    # class Method(Enum):
    #     """Mapping condition used."""
    #     dict = auto()
    #     counts = auto()
    #     rlabel = auto()
    #     manual = auto()

    def __init__(self, source_id, target_id, method='', info=''):
        self.source_id = source_id
        self.target_id = target_id
        self.info = info
        self.method = method

    def __repr__(self):
        return '{}->{} ({})'.format(self.source_id, self.target_id, self.method)


class Iteration:
    """Status of Relaxation Labeling algorithm."""
    def __init__(self, statistics, name=None):
        self._statistics = statistics
        # Dict with source id as key
        self.mappings = {}
        self.remaining = {}

        # We have not found any target candidates (using translations)
        self.no_candidates = set()
        # We have not found source in translations.
        self.no_translations = set()

        self.iteration = name
        # self.iteration
        # self.iteration results.
        # I Could have Iteration Results! Only iterations which have changes are noted,
        # and only the changes are saved! mapped is checked in all iterations!

    def copy(self, name=None):
        state = Iteration(self._statistics, name)
        state.mappings = copy.deepcopy(self.mappings)
        state.remaining = copy.deepcopy(self.remaining)
        state.no_translations = self.no_translations
        return state

    def name(self):
        return self._name

    def monosemous(self):
        pass

    def polysemous(self):
        pass

    def mappings(self):
        pass

    def remaining(self):
        pass

    def no_translations(self):
        pass

    def mapping_stats(self):
        # logger.info('remaining {}; no translations {}; translated: {}, using weights: {}'
        #             .format(remaining_c, not_translated, translated, using_weights))
        # logger.info('no_translations: {}, no_translations_lu: {}'
        #             .format(len(no_translations), len(no_translations_lu)))
        pass


class Statistics:
    """Status of Relaxation Labeling algorithm."""
    def __init__(self, wnsource, wntarget, to_map, dictionary=None):
        self.wnsource = wnsource
        self.wntarget = wntarget
        self.dictionary = dictionary
        self.iterations = [Iteration(self)]
        self.to_map = to_map
        # Only one translation found. Doesn't change with iterations.
        self.one_translation = {}
        # Dict with source id as key
        self.no_translations = set()

    def push_iteration(self, name=None):
        iter = self.iteration().copy(name)
        self.iterations.append(iter)

    # Could be a yield
    def mapped(self):
        combined = []
        for state in self.iterations:
            combined.extend(state.mappings)

    def in_mapped(self, source_id):
        for state in self.iterations:
            if source_id in state.mappings:
                return True
        return False

    def pop_iteration(self):
        self.iterations.pop()

    def iteration(self):
        return self.iterations[-1]

    def wordnet_info(self):
        logger.info('Translations, count: {}'.format(len(self.dictionary)))
        logger.info('Source synsets, count: {}'.format(len(self.wnsource.synsets_all())))
        logger.info('Target synsets, count: {}'.format(len(self.wntarget.synsets_all())))
