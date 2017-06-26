# -*- coding: utf-8 -*-
import logging

import numpy as np
import time

from collections import defaultdict

from pyrelaxmapper import dicts

logger = logging.getLogger()


class Node:
    """RL variable, a source taxonomy synset, with target labels.

    Parameters
    ----------
    source : int
    labels : array_list of int
    """

    def __init__(self, source, labels):
        self.source = source
        self.labels = labels
        self.weights = None
        self.weights_reset()

    def weights_reset(self):
        """Reset labels weights to their defaults."""
        if self.weights is None:
            self.weights = np.full(self.count(), self.avg_weight())
        else:
            self.weights.fill(self.avg_weight())

    def no_changes(self):
        """Whether the weights were changed from their defaults.

        Returns
        -------
        bool
        """
        return all(np.unique(self.weights) == self.avg_weight())

    def count(self):
        """Count of labels.

        Returns
        -------
        int
        """
        return len(self.labels)

    def avg_weight(self):
        """Average weight.

        Returns
        -------
        float
        """
        return 1 / self.count()

    def add_weight(self, idx, amount):
        """Increase one weight and proportionally decrease others."""
        sub = amount / (len(self.weights) - 1)
        self.weights -= sub
        self.weights[idx] += sub + amount


class Iteration:
    """Status of Relaxation Labeling algorithm.

    Parameters
    ----------
    status : Status
    index : int
        Iteration index.
    """

    def __init__(self, status, index=0):
        self._status = status
        self.mappings = {}
        self.remaining = {}
        self.index = index + 1
        self.time_sum = defaultdict(float)
        self.time = defaultdict(float)
        self.count = defaultdict(int)

    def changed(self):
        return len(self.mappings) > 0 or len(self.remaining) > 0

    def start(self, key):
        self.time[key] = time.clock()

    def stop(self, key):
        self.time[key] = time.clock() - self.time[key]
        self.time_sum[key] += self.time[key]

    def add_count(self, key, count):
        self.count[key] += count

    def avg(self, key):
        return self.time_sum[key] / self.count[key] if self.count[key] else 0


class Status:
    """Status of Relaxation Labeling algorithm.

    Parameters
    ----------
    config : pyrelaxmapper.conf.Config
    """

    def __init__(self, config):
        self.config = config
        self.mappings = {}
        self.relaxed = {}
        self.remaining = {}

        self.manual = {}
        # Manual which are missing in target
        self.d_missing = {}
        self.candidates = {}
        self.s_lemma_coverage = 0
        self.d_lemma_coverage = 0
        self.s_lemma_count = 0
        self.d_lemma_count = 0
        self.monosemous = {}
        self.polysemous = {}

        self._load_cache()
        self.mappings.update(self.monosemous)
        self.remaining.update(self.polysemous)
        self.iterations = [Iteration(self)]

    def source_wn(self):
        return self.config.source_wn()

    def target_wn(self):
        return self.config.target_wn()

    # lemma to synsets should be inside the wordnet! Or in config?
    def find_candidates(self):
        cache = self.config.cache
        if not cache.exists('Candidates', True):
            translater = self.config.dicts()
            source_lemmas = cache.rw_lazy('lemma -> synsets', self.source_wn().lemma_synsets,
                                          [self.config.cleaner], group=self.source_wn().name())
            target_lemmas = cache.rw_lazy('lemma -> synsets', self.target_wn().lemma_synsets,
                                          [self.config.cleaner], group=self.target_wn().name())
            args = [source_lemmas, target_lemmas, translater]
            (self.candidates, ((self.s_lemma_coverage, self.s_lemma_count),
                               (self.d_lemma_coverage, self.d_lemma_count))) \
                = cache.rw_lazy('Candidates', dicts.find_candidates, args, True)
        else:
            (self.candidates, ((self.s_lemma_coverage, self.s_lemma_count),
                               (self.d_lemma_coverage, self.d_lemma_count))) \
                = cache.r('Candidates', True)
        self.source_wn()._count_lemmas = self.s_lemma_count
        self.target_wn()._count_lemmas = self.d_lemma_count
        return self.candidates

    def _load_cache(self):
        """Find candidates or load them from cache."""
        cache = self.config.cache

        self.candidates = self.find_candidates()
        self.manual, self.d_missing = \
            cache.rw_lazy('Manual', self.source_wn().mappings, [self.target_wn()], True)

        if not self.candidates:
            self.candidates = {k.uid(): [k.uid()] for k in self.source_wn().all_synsets()}

        # Not convinced set wouldn't be better!
        self.monosemous = {source_id: list(target_ids)[0] for source_id, target_ids in
                           self.candidates.items() if len(target_ids) == 1}
        self.polysemous = {source_id: Node(source_id, list(target_ids))
                           for source_id, target_ids in
                           self.candidates.items() if len(target_ids) > 1}

    def push_iteration(self):
        """Save current iteration's results and create a new iteration.

        Returns
        -------
        Iteration
            The new iteration.
        """
        # All mappings
        self.mappings.update(self.iteration().mappings)
        # Relaxed mappings
        self.relaxed.update(self.iteration().mappings)
        # Learnt something, eliminated some labels.
        self.remaining.update(self.iteration().remaining)
        # Remove mapped objects from remaining.
        for key in self.iteration().mappings.keys():
            del self.remaining[key]

        self.iterations.append(Iteration(self, self.iteration().index))
        return self.iteration()

    def iteration(self):
        """Current iteration."""
        return self.iterations[-1]

    def pop_iteration(self):
        """Pop last iteration."""
        if len(self.iterations) > 0:
            del self.iterations[-1]
