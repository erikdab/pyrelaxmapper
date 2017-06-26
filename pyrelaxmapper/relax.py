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
        # Load on demand (because of eval_relax)
        # Or creat
        self.constrainer = config.constrainer()
        self.status = Status(self.config)
        self.stats = Stats(self.status)

    def save_stats(self, file):
        writer = csv.writer(file, delimiter='\t')
        writer.writerows(self.stats.stat_final().items())

    def relax(self):
        """Run relaxation labeling with all constraints in config."""
        self._relax_loop(self.constrainer)

    def eval_relax(self):
        """Run relaxation labeling evaluating constraint combinations."""
        # Series of combinations selected by the user!
        # Create
        # Maybe groups? And only all elements in groups are iterated over
        for constraint in []:
            self._relax_loop(self.constrainer)

    def _relax_loop(self, constrainer):
        iteration = self.status.iteration()
        writer = csv.writer(sys.stdout, delimiter='\t')
        while iteration.index <= 1 or self.status.iterations[-2].changed():
            key = 'iteration'
            iteration.start(key)
            iteration.add_count(key, len(self.status.remaining))
            click.secho('Iteration: {}'.format(iteration.index), fg='blue')
            self._relax(constrainer)
            iteration.stop(key)
            writer.writerows(self.stats.stat_iteration(iteration, True).items())
            # sys.exit(1)
            if not iteration.changed():
                break
            iteration = self.status.push_iteration()
        writer.writerows(self.stats.stat_total().items())

    def _relax(self, constrainer):
        todo = self.status.remaining.values()
        with click.progressbar(todo, label='Constraining nodes:') as nodes:
            # for node in nodes:
            for idx, node in enumerate(nodes):
                # if idx > 0 and idx % 50 == 0:
                #     return
                # Perhaps will find CHANGE rather than reset? Look at article
                node.weights_reset()

                constrainer.apply(self.status.mappings, node)

                # Makes sense, doesn't work.
                # node.weights = utils.normalized(node.weights)
                # Perhaps will find CHANGE rather than drop all others?
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
