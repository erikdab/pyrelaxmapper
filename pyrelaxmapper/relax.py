# -*- coding: utf-8 -*-
import logging

import click
import numpy as np

from pyrelaxmapper.status import Status
from pyrelaxmapper.stats import Stats

logger = logging.getLogger()


class Relaxer:
    """Relaxation Labeling WordNet Mapping Main algorithm class.

    Parameters
    ----------
    config : pyrelaxmapper.conf.Config
    """
    def __init__(self, config):
        self.config = config
        self.constrainer = config.constrainer()
        self.status = Status(self.config)
        self.stats = Stats(self.status)

    def relax(self):
        """Run relaxation labeling"""
        iteration = self.status.iteration()

        # Stopping Condition
        while iteration.index() <= 1 or self.status.iterations[-2].has_changes():
            self._iteration_relax()
            self.stats.stats_iteration(iteration)
            iteration = self.status.push_iteration()

    def _iteration_relax(self):
        iteration = self.status.iteration()
        remaining = self.status.remaining
        logger.info('Resetting weights.')
        for node in remaining.values():
            node.weights_reset()

        with click.progressbar(remaining.values(), label='Relaxing nodes') as nodes:
            for node in nodes:
                self.constrainer.apply(self.status.mappings, node)

        logger.info('Normalizing weights.')
        # for node in iteration.remaining.values():
        # for node in temp:
        #     node.weights = utils.normalized(node.weights)

        logger.info('Saving changes.')
        # for node in iteration.remaining.values():
        for node in remaining.values():
            self._iteration_changes(node)

    def _iteration_changes(self, node):
        """Write results for changed and not changed mappings."""
        iteration = self.status.iteration()
        weights = node.weights

        # Learnt nothing
        if node.no_changes():
            return

        maxind = np.argwhere(weights == np.amax(weights))[0]

        # Learnt nothing
        if len(maxind) == len(weights):
            return

        # Learnt something
        if len(maxind) == 1:
            # Monosemic mapping
            iteration.mappings[node.source()] = node.labels()[maxind[0]]
        else:
            # Polysemic lesson
            iteration.remaining[node.source()] = [node.labels()[idx] for idx in maxind]
