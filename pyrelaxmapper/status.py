# -*- coding: utf-8 -*-
import logging

import numpy as np

from pyrelaxmapper import dicts

logger = logging.getLogger()


class Connection:
    """Primarily for statistical purposes."""

    def __init__(self, constraint, weight):
        self.constraint = constraint
        self.weight = weight

    def update_weight(self, weight):
        pass


class Label:
    def __init__(self):
        self.connections = []
        self.weight = 0.0
        self.target = 0


class Node:
    """RL Label between source unit and target candidate

    Parameters
    ----------
    source : int
    labels : array_like
    weights : np.ndarray
    """
    def __init__(self, source, labels, weights=None):
        self._source = source
        self._labels = labels
        self.weights = None
        if weights is None:
            self.weights_reset()
        else:
            self.weights = weights

    def weights_reset(self):
        """Reset labels weights to their defaults."""
        if self.weights is None:
            self.weights = np.full(len(self._labels), self.avg_weight())
        else:
            self.weights.fill(self.avg_weight())
        # Also inside connections

    def no_changes(self):
        """Whether the weights were changed from their defaults.

        Returns
        -------
        bool
        """
        return len(np.unique(self.weights)) == 1

    def source(self):
        """Source variable uid.

        Returns
        -------
        int
        """
        return self._source

    def labels(self):
        """Target label ids.

        Returns
        -------
        array_like
        """
        return self._labels

    def avg_weight(self):
        """Average weight.

        Returns
        -------
        float
        """
        return 1 / len(self._labels)

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

        self.no_candidates = set()
        self.no_translations = set()

        self._index = index + 1

    def index(self):
        """Return iteration number.

        Returns
        -------
        int
        """
        return self._index

    def has_changes(self):
        return len(self.mappings) > 0 or len(self.remaining) > 0


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
        self.remaining = {}

        self._candidates = {}
        self.monosemous = {}
        self.polysemous = {}

        self.load_cache()
        self.mappings.update(self.monosemous)
        self.remaining.update(self.polysemous)
        self.iterations = [Iteration(self)]

    def load_cache(self):
        """Find candidates or load them from cache."""
        self._candidates = self.config.cache(self.config.file_candidates(), dicts.find_candidates,
                                             [self.source_wn, self.target_wn,
                                              self.config.cleaner(),
                                              self.config.translater()])

        self.monosemous = {source_id: target_ids[0] for source_id, target_ids in
                           self._candidates.items() if len(target_ids) == 1}
        # self.polysemous = {source_id: Node(source_id, target_ids) for source_id, target_ids in
        #                    enumerate(self._candidates.items()) if len(target_ids) > 1}
        idx = 0
        for source_id, target_ids in self._candidates.items():
            if idx == 3000:
                break
            if len(target_ids) > 1:
                self.polysemous[source_id] = Node(source_id, target_ids)
                idx += 1

    def push_iteration(self):
        """Save current iteration's results and create a new iteration.

        Returns
        -------
        Iteration
            The new iteration.
        """
        self.mappings.update({k: v for k, v in self.iteration().mappings.items()})
        self.remaining.update({k: v for k, v in self.iteration().remaining.items()})
        # Erase mapped objects.
        for key in self.iteration().mappings.keys():
            del self.remaining[key]

        self.iterations.append(Iteration(self, self.iteration().index()))
        return self.iteration()

    def iteration(self):
        """Current iteration."""
        return self.iterations[-1]
