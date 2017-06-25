# -*- coding: utf-8 -*-
import logging

import numpy as np
import time

from collections import defaultdict

from pyrelaxmapper import dicts

logger = logging.getLogger()


class Connection:
    """Primarily for statistical purposes."""

    def __init__(self, constraint, weight):
        self.constraint = constraint
        self.weight = weight


class Label:
    """A label between a source synset and a target synset."""

    def __init__(self, target):
        self.connections = []
        self.target = 0


class Node:
    """RL variable, a source taxonomy synset, with target labels.

    Parameters
    ----------
    source : int
    labels : array_list of int
    """

    def __init__(self, source, labels):
        self._source = source
        self._labels = labels
        # self._labels = [Label(label) for label in labels]
        self.weights = None
        self.weights_reset()

    def weights_reset(self):
        """Reset labels weights to their defaults."""
        if self.weights is None:
            self.weights = np.full(self.count(), self.avg_weight())
        else:
            self.weights.fill(self.avg_weight())
            # Also inside connections

    def no_changes(self):
        """Whether the weights were changed from their defaults.

        Returns
        -------
        bool
        """
        return all(np.unique(self.weights) == self.avg_weight())

    def source(self):
        """Source variable uid.

        Returns
        -------
        int
        """
        return self._source

    def labels_ids(self):
        """Target label ids.

        Returns
        -------
        array_like
        """
        return [label.target for label in self._labels]

    def labels(self):
        """Target label ids.

        Returns
        -------
        array_like of Label
        """
        return self._labels

    def count(self):
        """Count of labels.

        Returns
        -------
        int
        """
        return len(self._labels)

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
        self.weights[idx] += 2 * amount


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
        self._index = index + 1
        self.time_sum = defaultdict(float)
        self.time = defaultdict(float)
        self.count = defaultdict(float)

    def index(self):
        """Return iteration number.

        Returns
        -------
        int
        """
        return self._index

    def has_changes(self):
        return len(self.mappings) > 0 or len(self.remaining) > 0

    def start(self, key):
        self.time[key] = time.clock()

    def stop(self, key):
        self.time[key] = time.clock() - self.time[key]
        self.time_sum[key] += self.time[key]
        self.count[key] += 1

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
        self.source_wn = config.source_wn()
        self.target_wn = config.target_wn()
        self.mappings = {}
        self.relaxed = {}
        self.remaining = {}

        self.manual = {}
        self.candidates = {}
        self.monosemous = {}
        self.polysemous = {}

        self.load_cache()
        self.mappings.update(self.monosemous)
        self.remaining.update(self.polysemous)
        self.iterations = [Iteration(self)]

    def load_cache(self):
        """Find candidates or load them from cache."""
        cache = self.config.cache

        args = [self.source_wn, self.target_wn, self.config.cleaner, self.config.translater]
        self.candidates = cache.rw_lazy('Candidates', dicts.find_candidates, args, True)
        self.manual = cache.rw_lazy('Manual', self.source_wn.mappings, [self.target_wn], True)

        self.monosemous = {source_id: target_ids[0] for source_id, target_ids in
                           self.candidates.items() if len(target_ids) == 1}
        self.polysemous = {source_id: Node(source_id, target_ids) for source_id, target_ids in
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

        self.iterations.append(Iteration(self, self.iteration().index()))
        return self.iteration()

    def iteration(self):
        """Current iteration."""
        return self.iterations[-1]

    def pop_iteration(self):
        if len(self.iterations) > 0:
            del self.iterations[-1]
