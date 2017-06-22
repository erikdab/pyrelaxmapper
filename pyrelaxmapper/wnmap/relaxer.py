# -*- coding: utf-8 -*-
import logging

import numpy as np

logger = logging.getLogger()


class Relaxer:
    def run_relax(self):
        """Main relaxation function."""
        pass

    def normalize(self):
        """Normalize all label lists."""
        pass

    def nr_iter(self):
        pass

    def epsilon(self):
        pass

    def relax_edges(self):
        pass


def rl_loop(stats):
    """Relation Labeling iterations.

    Parameters
    ----------
    stats : pyrelaxmapper.wnmapper.stats.Statistics
    config : pyrelaxmapper.wnmapper.wnconfig.WNConfig
    """
    two(stats)
    # iteration = 0
    # measures = None
    # # TODO: Completion condition ! This needs to be analyzed
    # while iteration == 0 or sum(measures[:3]):
    #     if os.path.exists(conf.results('step2.txt')):
    #         with open(conf.results('step2.txt'), 'r', encoding='utf-8') as step2, \
    #                 open(conf.results('mapped.txt'), 'a', encoding='utf-8') as mapped:
    #             mapped.write(step2.read())
    #         os.remove(conf.results('step2.txt'))
    #     time_, measures = two(stats, config)
    #     logger.info('Iteration #{}: {}'.format(iteration, time_))
    #     logger.info('Summary : {}'.format(measures))
    #     # TODO: All iterations thingies with stats here.
    #     iteration += 1
    # return measures


# Inside stats.
# def _load_two():
#     mapped = {}
#     with open(conf.results('mapped.txt'), 'r', encoding='utf-8') as file:
#         for line in file:
#             cols = line.replace('*manually_added:', '').strip().split()
#             mapped[int(cols[0])] = str(cols[1])
#         logger.info('Load already mapped: {}'.format(len(mapped)))
#
#     remaining = {}
#     with open(conf.results('remaining.txt'), 'r', encoding='utf-8') as file:
#         done_count = 0
#         for line in file:
#             cols = (line.strip()).split()
#             if int(cols[0]) not in mapped:
#                 remaining[cols[0]] = cols[1:]
#             else:
#                 done_count += 1
#         logger.info('Loaded remaining expect for already done: {}'.format(done_count))

    # hipernyms = {}
    # with open(conf.results('synset_hipernyms.txt'), 'r', encoding='utf-8') as file:
    #     for line in file:
    #         cols = (line.strip()).split()
    #         hipernyms.setdefault(int(cols[0]), []).append(int(cols[1]))
    #     logger.info('Loaded synset hipernyms relations.')
    #
    # hiponyms = {}
    # with open(conf.results('synset_hiponyms.txt'), 'r', encoding='utf-8') as file:
    #     for line in file:
    #         cols = (line.strip()).split()
    #         hiponyms.setdefault(int(cols[0]), []).append(int(cols[1]))
    #     logger.info('Loaded synset hiponyms relations.')
    #
    # syns_text = {}
    # with open(conf.results('synsets_text.txt'), 'r', encoding='utf-8') as file:
    #     for line in file:
    #         cols = (line.strip()).split()
    #         syns_text[int(cols[0])] = cols[1:]
    #     logger.info('Loaded synset text.')
    # return mapped, remaining, hipernyms, hiponyms, syns_text
    # return mapped, remaining


# # TODO: Place inside stats
def _write_results(node, iteration):
    """Write results for changed and not changed mappings."""
    weights = node.weights()
    avg_weight = node.avg_weight()

    if np.all(weights == (np.ones(len(weights))) * avg_weight):
        # info = '{} {}\n'.format(, ' '.join([str(cand) for cand in candidates]))
        # no_changes.write(info)
        return

    best = np.nonzero([m == max(weights) for m in weights])
    if not (best and best[0]):
        return
    maxind = best[0][0]
    iteration.mappings[node.source()] = node.labels()[maxind]
    # try:
    #     maxind = np.nonzero([m == max(weights) for m in weights])[0]
    # except IndexError:
    #     logger.debug('Can not find candidates..')
    #     maxind = 0
    # step2.write(str(current_syn) + " " + str(candidates[maxind[0]]) + "\n")
    # mapped_count = mapped_count + 1


def two(stats):
    """Relaxation labeling iterations"""
    # Unpacking variables
    relaxmapper = stats.relaxmapper
    # config = relaxmapper.config
    # orig = relaxmapper.orig
    # dest = relaxmapper.dest
    # key: constraint, value: weight of constraint
    # constr = config.constraints
    # constr_weights = config.constr_weights
    iteration = stats.iteration()

    for node in iteration.remaining.values():
        node.reset_weights()

    relaxmapper.constrainer.apply(stats.mappings, iteration.remaining)

    for node in iteration.remaining.values():
        _write_results(node, iteration)

    # toc = time.clock()
    # step2.close()
    # no_changes.close()

    # logger.info("time: {}".format(toc - tic))
    # logger.info("Suggestions: {}".format(suggestions))
    # logger.info("Accepted by user: {}".format(selected))
    # logger.info("Selected by algorithm: {}".format(mapped_count))
    #
    # return np.array([toc - tic, suggestions, selected, mapped_count])
