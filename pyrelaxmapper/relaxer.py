# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger()


class Relaxer:
    """Relaxation Labeling WordNet Mapping Main algorithm class.

    Parameters
    ----------
    config : pyrelaxmapper.wnmap.wnconfig.WNConfig
    """
    def __init__(self, config):
        self.config = config
        self.constrainer = config.constrainer()
        # self.status = Status(self.config)

    def relax(self):
        """Run relaxation labeling"""
        # Completion condition
        # while :
        if True:
            self._relax_iteration()
            # stats.printIteration()
            # status.push_iteration()

    def normalize(self):
        """Normalize all label lists."""
        pass

    def _iteration_relax(self):
        pass
        # for node in iteration.remaining.values():
        #     node.reset_weights()
        # self.constrainer.apply(stats.mappings, iteration.remaining)
        # for node in iteration.remaining.values():
        #     self._iteration_results(node)

    def _iteration_results(self, node):
        """Write results for changed and not changed mappings."""
        # iteration = self.status.iteration()
        # weights = node.weights()
        # avg_weight = node.avg_weight()
        #
        # if np.all(weights == (np.ones(len(weights))) * avg_weight):
        #     # info = '{} {}\n'.format(, ' '.join([str(cand) for cand in candidates]))
        #     # no_changes.write(info)
        #     return
        #
        # best = np.nonzero([m == max(weights) for m in weights])
        # if not (best and best[0]):
        #     return
        # maxind = best[0][0]
        # iteration.mappings[node.source()] = node.labels()[maxind]
        # try:
        #     maxind = np.nonzero([m == max(weights) for m in weights])[0]
        # except IndexError:
        #     logger.debug('Can not find candidates..')
        #     maxind = 0
        # step2.write(str(current_syn) + " " + str(candidates[maxind[0]]) + "\n")
        # mapped_count = mapped_count + 1
