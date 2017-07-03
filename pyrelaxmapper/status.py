# -*- coding: utf-8 -*-
import logging

import numpy as np
import time

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

        self.time_sum = 0.0
        self.time = 0.0
        self.counter = 0

    def any_changes(self):
        """Were there any changes in the iteration."""
        return len(self.mappings) > 0 or len(self.remaining) > 0

    def time_start(self):
        """Start timer."""
        self.time = time.clock()

    def time_stop(self):
        """Stop timer and add time to self.time."""
        self.time = time.clock() - self.time
        self.time_sum += self.time

    def add_count(self, count):
        """Increment progress counter."""
        self.counter += count

    def time_avg(self):
        """Average time"""
        return self.time_sum / self.counter if self.counter else 0


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
        self.candidates = {}
        self.monosemous = {}
        self.polysemous = {}

        self.load()
        self.mappings.update(self.monosemous)
        self.remaining.update(self.polysemous)
        self.iterations = [Iteration(self)]

    def source_wn(self):
        """Mapping source wordnet."""
        return self.config.source_wn()

    def target_wn(self):
        """Mapping target wordnet."""
        return self.config.target_wn()

    def load(self):
        """Load required information."""
        self.candidates = self.config.candidates()
        self.manual = self.config.manual()

        if not self.candidates:
            self.candidates = {k.uid(): [k.uid()] for k in self.source_wn().all_synsets()}

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
        self.mappings.update(self.iteration().mappings)
        self.relaxed.update(self.iteration().mappings)
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
