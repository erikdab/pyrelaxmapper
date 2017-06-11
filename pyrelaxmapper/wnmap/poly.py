# -*- coding: utf-8 -*-
import logging
import os
import time

import numpy as np

from pyrelaxmapper import conf
from pyrelaxmapper.plwordnet.plsource import PLWordNet
from pyrelaxmapper.pwn.psource import PWordNet
from pyrelaxmapper.wnmap import constraint, wnutils

logger = logging.getLogger()


def rl_loop(c='ii', m='t'):
    """Relation Labeling iterations."""
    iteration = 0
    measures = None
    # TODO: Completion condition ! This needs to be analyzed
    while iteration == 0 or sum(measures[:3]):
        if os.path.exists(conf.results('step2.txt')):
            with open(conf.results('step2.txt'), 'r', encoding='utf-8') as step2, \
                    open(conf.results('mapped.txt'), 'a', encoding='utf-8') as mapped:
                mapped.write(step2.read())
            os.remove(conf.results('step2.txt'))
        time_, measures = two(c, m)
        logger.info('Iteration #{}: {}'.format(iteration, time_))
        logger.info('Summary : {}'.format(measures))
        iteration += 1
    return measures


def _load_two():
    mapped = {}
    with open(conf.results('mapped.txt'), 'r', encoding='utf-8') as file:
        for line in file:
            cols = line.replace('*manually_added:', '').strip().split()
            mapped[int(cols[0])] = str(cols[1])
        logger.info('Load already mapped: {}'.format(len(mapped)))

    remaining = {}
    with open(conf.results('remaining.txt'), 'r', encoding='utf-8') as file:
        done_count = 0
        for line in file:
            cols = (line.strip()).split()
            if int(cols[0]) not in mapped:
                remaining[cols[0]] = cols[1:]
            else:
                done_count += 1
        logger.info('Loaded remaining expect for already done: {}'.format(done_count))

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
    return mapped, remaining


def _write_results(weights, current_syn, avg_weight, mapped_count, candidates, no_changes, step2):
    """Write results for changed and not changed mappings."""
    if np.all(weights == (np.ones(len(weights))) * avg_weight):
        info = '{} {}\n'.format(current_syn, ' '.join([str(cand) for cand in candidates]))
        no_changes.write(info)
        return

    try:
        maxind = np.nonzero([m == max(weights) for m in weights])[0]
    except IndexError:
        logger.debug('Can not find candidates..')
        maxind = 0
    step2.write(str(current_syn) + " " + str(candidates[maxind[0]]) + "\n")
    mapped_count = mapped_count + 1


# Status, Config
def two(constr, mode):
    """Relaxation labeling iterations"""
    step2 = open(conf.results('step2.txt'), 'w', encoding='utf-8')
    no_changes = open(conf.results('no_changes.txt'), 'w', encoding='utf-8')

    mapped, remaining = _load_two()

    parser = conf.load_conf()
    session = conf.make_session(parser)

    # Uncached: 13.664 sec., cached: 2.072 sec.
    logger.info('Loading plWordNet source.')
    source, from_cache = wnutils.cached(conf.results('cache_pl.pkl'), PLWordNet, [session])

    # Uncached: 17.885 sec., cached: 1.325 sec.
    logger.info('Loading PWN target.')
    target, from_cache = wnutils.cached(conf.results('cache_en.pkl'), PWordNet)

    # config = Config()
    # status = Status()
    # relaxer = Relaxer()

    # This kind of info should be inside a class!
    # line_nr = 0
    # which_one = 0
    suggestions = 0  # algorithm suggestions
    selected = 0  # algorithm suggestions accepted by the user
    mapped_count = 0  # algorithm selected without user interaction

    weight_hiper = 0.93
    weight_hipo = 1.0

    tic = time.clock()
    for current in remaining.items():
        # plWN source information
        source_syn = source.synset(current[0])
        hiper_pl, father_pl = wnutils.hiper_path(source_syn)
        hipo_pl, hipo_pl_layers, children_pl = wnutils.hipo(source_syn)

        candidates = current[1]
        avg_weight = 1. / len(candidates)  # initial weight for each mapping
        weights = (np.ones(len(candidates))) * avg_weight

        # traverse through target potential candidates.
        for idx, target_name in enumerate(candidates):
            target_syn = target.synset(target_name)
            hiper_en, father_en = wnutils.hiper_path(target_syn)
            hipo_en, hipo_en_layers, children_en = wnutils.hipo(target_syn)

            if constr in ['iie', 'ii']:
                constraint.iie(mapped, father_pl, father_en, weights, idx, weight_hiper,
                               avg_weight)

            if constr in ['iio', 'ii']:
                constraint.iio(mapped, children_pl, children_en, idx, weights, weight_hipo,
                               avg_weight)

            if constr in ['iib', 'ii']:
                constraint.iib(mapped, father_pl, father_en, children_pl, children_en, idx,
                               weights)

            if constr in ['aie', 'ai']:
                constraint.aie(mapped, father_en, hiper_pl, avg_weight, weight_hiper, idx, weights)

            if constr in ['aio', 'ai']:
                constraint.aio(mapped, hipo_pl, hipo_pl_layers, children_en, avg_weight,
                               weight_hipo, idx,
                               weights)

            if constr in ['aib', 'ai']:
                constraint.aib(mapped, hiper_pl, father_en, hipo_pl, hipo_pl_layers, children_en,
                               idx,
                               weights)

            if constr in ['iae', 'ia']:
                constraint.iae(mapped, father_pl, hiper_en, weight_hiper, avg_weight, idx,
                               weights)

            if constr in ['iao', 'ia']:
                constraint.iao(mapped, children_pl, hipo_en, weight_hipo, avg_weight,
                               hipo_en_layers,
                               idx, weights)

            if constr in ['iab', 'ia']:
                constraint.iab(mapped, father_pl, hiper_en, children_pl, hipo_en,
                               weight_hiper,
                               hipo_en_layers,
                               weight_hipo, idx, weights)

            if constr in ['aae', 'aa']:
                constraint.aae(mapped, hiper_pl, hiper_en, weight_hiper, avg_weight, idx,
                               weights)

            if constr in ['aao', 'aa']:
                constraint.aao(mapped, hipo_pl, hipo_en, avg_weight, weight_hipo,
                               hipo_pl_layers,
                               hipo_en_layers,
                               idx, weights)

            if constr in ['aab', 'aa']:
                constraint.aab(mapped, hiper_pl, hiper_en, hipo_en, hipo_pl,
                               hipo_pl_layers,
                               hipo_en_layers, idx, weights)

    toc = time.clock()
    step2.close()
    no_changes.close()

    logger.info("time: {}".format(toc - tic))
    logger.info("Suggestions: {}".format(suggestions))
    logger.info("Accepted by user: {}".format(selected))
    logger.info("Selected by algorithm: {}".format(mapped_count))

    return np.array([toc - tic, suggestions, selected, mapped_count])
