# -*- coding: utf-8 -*-
import csv
import logging
import sys

import click
import numpy as np

from pyrelaxmapper.stats import Stats
from pyrelaxmapper.status import Status

logger = logging.getLogger()


class Relaxer:
    """Relaxation Labeling WordNet Mapping Main algorithm class.

    Parameters
    ----------
    config : pyrelaxmapper.conf.Config
    """

    def __init__(self, config):
        self.config = config
        self.status = Status(self.config)
        self.stats = Stats(self.status)

    def relax(self):
        """Run relaxation labeling with all constraints in config."""
        key = 'iteration'
        writer = csv.writer(sys.stdout, delimiter='\t')

        status = self.status
        iteration = status.iteration()
        while iteration.index <= 1 or self.status.iterations[-2].changed():
            click.secho('Iteration: {}'.format(iteration.index), fg='blue')

            iteration.add_count(key, len(self.status.remaining))

            iteration.start(key)
            self._relax_loop()
            iteration.stop(key)

            writer.writerows(self.stats.stat_iteration(iteration, True).items())

            iteration = self.status.push_iteration()

        iteration = self.status.pop_iteration()
        writer.writerows(self.stats.stat_total().items())

    def _relax_loop(self):
        """Run relaxation labeling iteration for all remaining nodes."""
        remaining = self.status.remaining.values()
        with click.progressbar(remaining, label='Constraining nodes:') as nodes:
            for node in nodes:

                node.weights_reset()

                self.config.constrainer.apply(self.status, node)

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
            iteration.mappings[node.source] = node.labels[maxind[0]]
        else:
            # Polysemic lesson
            logger.info('Polysemic mapping done!')
            iteration.remaining[node.source] = [node.labels[idx] for idx in maxind]
