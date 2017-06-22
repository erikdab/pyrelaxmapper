# -*- coding: utf-8 -*-
import logging

import numpy as np

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


class Node:
    """RL Label between source unit and target candidate

    Parameters
    ----------
    vertex
    """

    def __init__(self, source, labels, weights=None):
        self._source = source
        self._labels = labels
        if weights is None:
            self.reset_weights()
        else:
            self._weights = weights

    def reset_weights(self):
        self._weights = np.ones(len(self._labels)) * self.avg_weight()

    def source(self):
        return self._source

    def labels(self):
        return self._labels

    def weights(self):
        return self._weights

    def avg_weight(self):
        return 1 / len(self._labels)

    def add_weight(self, idx, weight):
        if idx not in self._labels:
            raise KeyError('Node {} does not contain label of id: {}'.format(
                self._source.id_(), idx))
        decr = weight / len(self._labels)
        self._weights[idx] += weight
        self._weights[:idx] -= decr
        self._weights[idx:] -= decr


class Iteration:
    """Status of Relaxation Labeling algorithm."""
    def __init__(self, status, remaining, iteration=0):
        self._status = status
        self.mappings = {}
        self.remaining = remaining

        self.no_candidates = set()
        self.no_translations = set()

        self._iteration = iteration + 1

    def iteration(self):
        """Return iteration number.

        Returns
        -------
        int
        """
        return self._iteration


class Statistics:
    """Status of Relaxation Labeling algorithm."""
    def __init__(self, config):
        self.config = config
        # Links
        # self.wnsource = None
        # self.wntarget = None
        self.iterations = [Iteration(self, config.polysemous())]
        # + Already mapped
        self.mappings = config.monosemous()
        # self.dictionary = None
        # self.monosemous = None
        # self.polysemous = None
        # Only one translation found. Doesn't change with iterations.
        # self.one_translation = {}
        # Dict with source id as key
        # List of lemmas with no translation
        # List of synsets with no candidates
        # self.no_translations = set()

    def candidates(self):
        pass
        # if not self._candidates:
        #     candidates_file = '({} -> {}) Candidates'.format(self.orig.name(), self.dest.name())
        #     # Translater for multi-lingual
        #     self._candidates = wnutils.cached(candidates_file, translate.find_candidates,
        #                                       [self.orig, self.dest, wnutils.clean])
        # return self._candidates

    def cached(self):
        pass
        # Intermediary, not necessary to save.
        # candidates_file = '({} -> {}) Candidates'.format(self.orig.name(), self.dest.name())
        # self._candidates = wnutils.cached(candidates_file, self.candidates)
        #
        # self._monosemous = {source_id: target_ids for source_id, target_ids in
        #                     self._candidates.items() if len(target_ids) == 1}
        # self._polysemous = {source_id: Node(source_id, target_ids) for source_id, target_ids in
        #                     self._candidates.items() if len(target_ids) > 1}

    def push_iteration(self):
        it = self.iteration()
        self.mappings.extend(it.mappings)
        next_it = Iteration(self, it.remaining, it.iteration())
        self.iterations.append(next_it)
        return self.iteration()

    def iteration(self):
        return self.iterations[-1]
