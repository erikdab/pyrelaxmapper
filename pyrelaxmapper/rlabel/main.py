# -*- coding: utf-8 -*-
import os
import random
import time
import logging
# from functools import partial
import pickle

import numpy as np
from nltk.corpus import wordnet as pwn

from pyrelaxmapper.pwn.psource import PWordNet
from pyrelaxmapper import conf
from pyrelaxmapper.plwordnet.plsource import PLWordNet
from pyrelaxmapper.rlabel import rlutils

logger = logging.getLogger()


def _load_data():
    """Load input data: translations, synsets, units."""

    # { word : [translation_1, translation_2, ...] }
    with open(conf.results('translations.txt'), 'r', encoding='utf-8') as file:
        dictionary = {}
        for line in file:
            line = (line.strip()).split()
            dictionary[line[0]] = line[1:]

    # { nr_synset : [LU_1, LU_2, ...] }
    with open(conf.results('synsets.txt'), 'r', encoding='utf-8') as file:
        synsets = {}
        for line in file:
            line = (line.strip()).split()
            synsets[line[0]] = line[1:]

    # { nr_LU : 'word' }
    with open(conf.results('units.txt'), 'r', encoding='utf-8') as file:
        lunits = {}
        for line in file:
            line = (line.strip()).split()
            lunits[line[0]] = line[1]
    return dictionary, synsets, lunits


def _translate_lunit(lunit_ids, lunits, dictionary):
    """Search for translation for lexical unit."""
    not_found = set()
    translations = set()
    for lunit_id in lunit_ids:
        if lunit_id not in lunits:
            logger.debug('LU {} cannot be found!'.format(lunit_id))
        word = lunits[lunit_id] if lunit_id in lunits else ''
        if word in dictionary:
            translations.update([translation.lower() for translation in dictionary[word]])
        else:
            not_found.add(word)

    return list(not_found), list(translations)


def _search_pwn(source, translations):
    """Get PWN synsets matching translations."""
    pwn_synsets = set()
    for term in translations:
        try:
            pwn_synsets.update(pwn_synset.name() for pwn_synset in pwn.synsets(term))
        except AttributeError:
            logger.debug(("AttributeError: blad najprawdopodobniej w wordnet.py; "
                          "miejsce w programie: ") + source + " - " + term + " - " + str(
                translations))
    return list(pwn_synsets)


def _mapping_info(source, lunits, synsets, pwn_synsets, weights):
    """Format information about mappings."""
    # if weights is None:
    #     weights = np.array([1])

    pl_lunits = []
    try:
        pl_lunits = [lunits[syn] for syn in synsets[source]]
    except KeyError:
        logger.info('KeyError in synset {} -> {}'.format(source, str(pwn_synsets)))

    pwn_info = []
    for i in weights.nonzero()[0]:
        synset = pwn_synsets[i]
        lemmas = pwn.synset(synset).lemma_names()
        pwn_info.append('{}: {}'.format(synset, lemmas))
    mapping_info = '{} {} -> {}\n'.format(source, str(pl_lunits), ' | '.join(pwn_info))
    mappings = '{} {}\n'.format(source, ' '.join(pwn_synsets[i] for i in weights.nonzero()[0]))
    return mappings, mapping_info


def _stat_weights(weights, source, pwn_synsets):
    # Statistics: If there is at least one weight==0, then we can eliminate it.
    # Therefore we have learnt something.
    # TODO: Consider how not important this is.. maybe remove
    # Writes about weights!
    nonzero_weights = len(weights.nonzero()[0])
    if len(weights) - nonzero_weights > 0:
        syn = ' '.join('{} {}'.format(syn, weights[i]) for i, syn in enumerate(pwn_synsets))
        '{} {}\n'.format(source, syn)


def _initial_weights(pwn_synsets, translations):
    """Set initial weights based on the number of translations in every synset."""
    weights = np.zeros(len(pwn_synsets))

    # TODO: Consider if we can filter out more? Or add more weights some how
    # Weights: sum of occurences of translations in synset
    for i, synset in enumerate(pwn_synsets):
        pwn_synset = pwn.synset(synset)
        terms = pwn_synset.lemma_names() + [pwn_synset.name()]
        weights[i] += sum(1 for t in translations if t in terms)

    candidates = len(weights.nonzero()[0])
    return weights, candidates


def one():  # pierwsza iteracja
    # LOAD FILES
    # ALREADY MAPPED
    mapped = open(conf.results('mapped.txt'), 'a', encoding='utf-8')
    # TO MAP
    remaining = open(conf.results('remaining.txt'), 'a', encoding='utf-8')

    # wynik z opisami synsetow
    # ALREADY MAPPED STATS
    mapped_info = open(conf.results('mapped_info.txt'), 'a', encoding='utf-8')
    # ???
    remaining_info = open(conf.results('remaining_info.txt'), 'a', encoding='utf-8')
    # EXTRA MEASURE STATS? What is it?
    remaining_info2 = open(conf.results('remaining_info2.txt'), 'a', encoding='utf-8')

    logger.info('Loading data.')
    dictionary, synsets, lunits = _load_data()
    logger.info('Loaded translations, count: {}'.format(len(dictionary)))
    logger.info('Loaded synsets, count: {}'.format(len(synsets)))
    logger.info('Loaded lexical units, count: {}'.format(len(lunits)))
    logger.info('Done.')

    # use pickle! Simplifies every step!
    # At the end of the algorithm, save to files for analysis.

    remaining_c = 0
    translated = 0
    not_translated = 0
    using_weights = 0
    mapped_list = []
    no_translations = []
    no_translations_lu = []
    logger.info('Starting monosemous mappings.')
    tic = time.clock()
    for synset in list(synsets.items()):
        source = str(synset[0])
        lunit_ids = synset[1]

        not_found, translations = _translate_lunit(lunit_ids, lunits, dictionary)
        no_translations_lu.append('LUs not found in dictionary {}->{}'
                                  .format(synset, ''.join(not_found)))

        pwn_synsets = _search_pwn(source, translations)

        weights = np.array([1])
        candidates = len(pwn_synsets)
        if candidates > 1:
            weights, candidates = _initial_weights(pwn_synsets, translations)

        if pwn_synsets:
            mappings, mapping_info = _mapping_info(source, lunits, synsets, pwn_synsets, weights)

        if candidates == 0:
            not_translated = not_translated + 1
            no_translations.append('Synset not found in dictionary {}: {}'
                                   .format(source, str(lunit_ids)))
        # Monosemous
        if candidates == 1:
            if source in mapped_list:
                continue
            translated += 1
            if len(pwn_synsets) > candidates:
                using_weights += 1

            mapped.write(mappings)
            mapped_info.write(mapping_info)
        # Polysemous
        else:
            remaining_c += 1
            remaining.write(mappings)
            remaining_info.write(mapping_info)

    toc = time.clock()
    logger.info('Time: {}; remaining {}; no translations {}; translated: {}, using weights: {}'
                .format(toc - tic, remaining_c, not_translated, translated, using_weights))
    logger.info('no_translations: {}, no_translations_lu: {}'
                .format(len(no_translations), len(no_translations_lu)))

    mapped.close()
    mapped_info.close()
    remaining.close()
    remaining_info.close()
    remaining_info2.close()
    with open(conf.results('no_translations.txt'), 'w', encoding='utf-8') as file:
        file.write('\n'.join(no_translations))
    with open(conf.results('no_translations_lu.txt'), 'w', encoding='utf-8') as file:
        file.write('\n'.join(no_translations_lu))


def _hip_pl(node, hip):
    """Direct hiponyms/hipernyms for plWN node."""
    return [node_hip for node_hip in hip[node]] if node in hip else []


def _hipo_en(node):
    """Direct hiponyms for PWN node:"""
    return [hypo_node.name() for hypo_node in pwn.synset(node).hyponyms()]


def _hiper_en(synset):
    """Find hipernyms for PWN synset."""
    parent = []
    hipernyms = pwn.synset(synset).hypernym_paths()

    # TODO: For now only clear paths are used.
    if len(hipernyms) == 1:
        # Proper direction (synset -> hiper -> hiper of hiper). Don't take synset.
        hipernyms = [hiper.name() for hiper in hipernyms[0]][1::-1]
        parent = hipernyms[0]
    return hipernyms, parent


def _add_weight(weights, idx_add, amount):
    """Add to one weight, while decreasing others to keep balance."""
    sub = amount / (len(weights) - 1)
    for idx in range(len(weights)):
        weights[idx] += amount if idx == idx_add else -sub


def _iie(mapped, father_pl, father_en, weights, idx, weight_hipernym, average_weight):
    """Fathers and fathers."""
    if father_pl in mapped and mapped[father_pl] == father_en:
        weight_val = weight_hipernym * average_weight
        _add_weight(weights, idx, weight_val)


def _iio(mapped, children_pl, sons, idx, weights, weight_hiponym, average_weight):
    """Sons and sons."""
    for son in children_pl:
        if son in mapped and mapped[son] in sons:
            weight_val = weight_hiponym * average_weight
            _add_weight(weights, idx, weight_val)


def _iib(mapped, father_pl, father_en, children_pl, sons, idx, weights):
    """Sons and fathers on both."""
    if not (father_pl in mapped and mapped[father_pl] == father_en):
        return
    for syn in children_pl:
        if syn in mapped and mapped[syn] in sons:
            # 10 > 6 = average candidate length (look article)
            weight_val = 10. / (len(weights) * len(weights))
            _add_weight(weights, idx, weight_val)


def _aie(mapped, father_en, hipernyms_pl, avg_weight, weight_hiper, idx, weights):
    """Ancestor and father."""
    for ancestor in hipernyms_pl:
        if ancestor in mapped and mapped[ancestor] == father_en:
            distance = (hipernyms_pl.index(ancestor))
            weight_val = weight_hiper * avg_weight / (2 ** distance)
            _add_weight(weights, idx, weight_val)


def _aio(mapped, hiponyms_pl, hipo_pl_layers, sons, avg_weight, weight_hipo, idx, weights):
    """Descendant and child."""
    for descendant in hiponyms_pl:
        if descendant in mapped and mapped[descendant] in sons:
            distance = [descendant in p for p in hipo_pl_layers].index(True)
            weight_val = weight_hipo * avg_weight / (2 ** distance)
            _add_weight(weights, idx, weight_val)


def _aib(mapped, hipernyms_pl, father_en, hipo_pl, hipo_pl_layers, sons, idx, weights):
    """Ancestors/Descendent and father/son."""
    any_ = False
    dist_anc = 0
    for ancestor in hipernyms_pl:
        if ancestor in mapped and mapped[ancestor] == father_en:
            any_ = True
            dist_anc = hipernyms_pl.index(ancestor)
    if not any_:
        return
    for descendant in hipo_pl:
        if descendant in mapped and mapped[descendant] in sons:
            dist_desc = [descendant in p for p in hipo_pl_layers].index(True)
            weight_val = (15 / len(weights) ** 2) / (2 ** max(dist_anc, dist_desc))
            _add_weight(weights, idx, weight_val)


def _iae(mapped, father_pl, hipernyms_en, weight_hiper, avg_weight, idx, weights):
    """Father and ancestor."""
    if father_pl in mapped and mapped[father_pl] in hipernyms_en:
        distance = hipernyms_en.index(mapped[father_pl])
        weight_val = weight_hiper * avg_weight / (2 ** distance)
        _add_weight(weights, idx, weight_val)


def _iao(mapped, children_pl, hiponyms_en, weight_hipo, avg_weight, hipo_en_layers, idx, weights):
    """Sons and descendent"""
    for syn in children_pl:
        if syn in mapped and mapped[syn] in hiponyms_en:
            distance = [mapped[syn] in q for q in hipo_en_layers].index(True)
            weight_val = weight_hipo * avg_weight / (2 ** distance)
            _add_weight(weights, idx, weight_val)


def _iab(mapped, father_pl, hipernyms_en, children_pl, hiponyms_en, weight_hiper, hipo_en_layers,
         weight_hipo, idx, weights):
    """Father and ancestor + Son and descendent."""
    if not (father_pl in mapped and mapped[father_pl] in hipernyms_en):
        return
    weight_hiper = weight_hiper / (2 ** (hipernyms_en.index(mapped[father_pl])))
    for syn in children_pl:
        if syn in mapped and mapped[syn] in hiponyms_en:
            dist = ([mapped[syn] in q for q in hipo_en_layers].index(True))
            weight_val = 2. * weight_hiper + weight_hipo / (2. ** dist)
            _add_weight(weights, idx, weight_val)


def _aae(mapped, hipernyms_pl, hipernyms_en, weight_hiper, avg_weight, idx, weights):
    """Ancestor and ancestor."""
    for hipernym in hipernyms_pl:
        if hipernym in mapped and mapped[hipernym] in hipernyms_en:
            weight_val = weight_hiper * avg_weight / (
                2 ** max(hipernyms_pl.index(hipernym),
                         hipernyms_en.index(mapped[hipernym])))
            _add_weight(weights, idx, weight_val)


def _aao(mapped, hipo_pl, hiponyms_en, avg_weight, weight_hipo, hipo_pl_layers, hipo_en_layers,
         idx, weights):
    """Descendent and descendent."""
    for hipo in hipo_pl:
        if hipo in mapped and mapped[hipo] in hiponyms_en:
            weight_val = weight_hipo * avg_weight / (
                2 ** max([hipo in p for p in hipo_pl_layers].index(True),
                         [mapped[hipo] in q for q in hipo_en_layers].index(True)))
            _add_weight(weights, idx, weight_val)


def _aab(mapped, hipernyms_pl, hipernyms_en, hiponyms_en, hipo_pl, hipo_pl_layers,
         hipo_en_layers, idx, weights):
    """Descendents and ancestors"""
    any_ = False
    dist_pl = dist_en = 0
    for hiper in hipernyms_pl:
        if hiper in mapped and mapped[hiper] in hipernyms_en:
            any_ = True
            dist_pl = hipernyms_pl.index(hiper)
            dist_en = hipernyms_en.index(mapped[hiper])
    if not any_:
        return
    for hipo in hipo_pl:
        if hipo in mapped and mapped[hipo] in hiponyms_en:
            weight_val = (2 ** (
                [hipo in p for p in hipo_pl_layers].index(True) +
                [mapped[hipo] in q for q in hipo_en_layers]
                .index(True) + dist_pl + dist_en))
            # 10 > 6 = srednia liczba kandydatow (patrz artykul)
            weight_val = (20. / (len(weights) ** 2)) / weight_val
            _add_weight(weights, idx, weight_val)


class Status:
    """Status of Relaxation Labeling algorithm."""
    map_done = None
    map_todo = None

    all_weights = None
    all_candidates = None

    file_rlmap = None
    file_no_changes = None

    wn_source = None
    wn_target = None

    def __init__(self, config):
        pass


class Stats:
    """Statistics of Relaxation Labeling algorithm."""

    toc = time.clock()
    tic = time.clock()

    line_nr = 0
    which_one = 0
    suggestions = 0  # algorithm suggestions
    selected = 0  # algorithm suggestions accepted by the user
    mapped_count = 0  # algorithm selected without user interaction

    def __init__(self, config, status):
        self._config = config
        self.to_eval = self._select_eval(status.map_todo)

    def __str__(self):
        logger.info("time: {}".format(self.toc - self.tic))
        logger.info("Suggestions: {}".format(self.suggestions))
        logger.info("Accepted by user: {}".format(self.selected))
        logger.info("Selected by algorithm: {}".format(self.mapped_count))

    # TODO: Allow selecting which ones to evaluate
    def _select_eval(self, rest):
        """Select random elements for manual evaluation."""
        syn_ids = list(rest.keys())
        selected = set()
        while len(selected) < 5000:
            idx = random.randrange(len(rest))
            selected.add(syn_ids[idx])
        logger.info('Selected {} synsets to test manually\n'.format(len(selected)))
        return selected

    def _eval_prompt(self, suggestions, weights, syns_text, hiper_pl, hipo_pl, current_syn,
                     candidates, step2, line_nr, which_one, selected):
        """Manual evaluation prompt."""
        suggestions = suggestions + 1
        try:
            maxind = np.nonzero([m == max(weights) for m in weights])[0]
        except IndexError:
            logger.debug('Can not find candidates..')
            maxind = 0

        # Some synsets are empty...
        try:
            hipern_pl = [syns_text[s] for s in hiper_pl]
        except KeyError:
            logger.debug('Synset empty.')
            hipern_pl = []
        logger.info('Polish hipernyms: {}'.format(hipern_pl[0:5]))

        try:
            hipon_pl = [syns_text[s] for s in hipo_pl]
        except KeyError:
            logger.debug('Synset empty.')
            hipon_pl = []
        logger.info('Polish hiponyms: {}'.format(hipon_pl[0:5]))

        logger.info('Candidates count: {}'.format(len(weights)))
        logger.info('Candidates for {}:'.format(current_syn))
        for idx in range(len(weights)):
            # przegladamy potencjalne dopasowania - elementy tablicy kandydaci
            logger.info("\n", idx + 1, " ", candidates[idx], ": ",
                        pwn.synset(str(candidates[idx])).lemma_names())
            logger.info("\nhipernyms: ", [i.name() for i in
                                          pwn.synset(candidates[idx]).hypernym_paths()[0]][
                                         0:5])
            logger.info("\nhiponyms: ",
                        [i.name() for i in pwn.synset(candidates[idx]).hyponyms()][0:5], "\n")

        logger.info("\nAlgorithm selected:")
        if type(maxind) != list:
            maxind = [maxind]
        for n in range(len(maxind[0])):
            logger.info(maxind, maxind[0], maxind[0][n] + 1, " ",
                        candidates[int(maxind[0][n])])
        try:
            odp = input("\nSelect a candidate to assign (0-resign):")
            if odp != '0':
                line_nr = line_nr + 1
                which_one = which_one + 1
                step2.write(str(line_nr) + " " + str(current_syn) + " " + str(
                    candidates[int(odp) - 1]) + "\n")
                logger.info("\nans: ", odp, " Assigned ", candidates[int(odp) - 1], " do ",
                            current_syn,
                            ".\n")
                if int(odp) - 1 in maxind[0]:
                    selected = selected + 1
            odp = input("\nEnter any Key to continue")
        except ValueError:
            logger.info("Wrong value???")
        if which_one % 5 == 1:
            logger.info("Suggestions: ", suggestions)
            logger.info("Accepted by user: ", selected)
            odp = input("\nEnter any Key to continue")

    def _toeval(self):
        pass
        # if mode == 'i' and current_syn in to_eval:
        #     _eval_prompt(suggestions, weights, syns_text, hiper_pl, hipo_pl, current_syn,
        #                  candidates, step2, line_nr, which_one, selected)


class Relaxer:
    """Relaxation labeling relaxer."""
    _constraints = None


class Constraint:
    """A constraint to be used in Relaxation Labeling."""
    def __init__(self, status, weight):
        self._status = status
        self._weight = weight

    def apply(self):
        """Apply constraint."""
        pass


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

    # mapped, remaining, hiper, hipo, syns_text = _load_two()
    mapped, remaining = _load_two()

    parser = conf.load_conf()
    session = conf.make_session(parser)

    # Cache plWN
    cache_pl = conf.results('cache_pl.pkl')
    logger.info('Loading plWordNet source.')
    if os.path.exists(cache_pl):
        with open(cache_pl, 'rb') as file:
            source = pickle.load(file)
        logger.info('Loaded from cache.')
    else:
        source = PLWordNet(session)

        with open(cache_pl, 'wb') as file:
            pickle.dump(source, file, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info('Loaded from DB into cache.')
    source = None

    # Cache PWN
    cache_en = conf.results('cache_en.pkl')
    logger.info('Loading PWN target.')
    if os.path.exists(cache_en):
        with open(cache_en, 'rb') as file:
            target = pickle.load(file)
        logger.info('Loaded from cache.')
    else:
        target = PWordNet()

        with open(cache_en, 'wb') as file:
            pickle.dump(target, file, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info('Loaded from NLTK into cache.')

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
    # hiper_func_pl = partial(_hip_pl, hip=hiper)
    # hipo_func_pl = partial(_hip_pl, hip=hipo)
    for current in remaining.items():
        # plWN source information
        current_syn = int(current[0])
        candidates = current[1]
        source_syn = source.synset(current_syn)
        avg_weight = 1. / len(candidates)  # initial weight for each mapping
        weights = (np.ones(len(candidates))) * avg_weight

        hiper_pl, father_pl = rlutils.hiper(source_syn)
        hipo_pl, hipo_pl_layers, children_pl = rlutils.hipo(source_syn)

        # traverse through PWN target potential candidates.
        for idx, candidate in enumerate(candidates):
            candidate_ = target.synset(candidate)
            hiponyms_en, hipo_en_layers, __ = rlutils.hipo(candidate_)
            hipernyms_en, father_en = rlutils.hiper_path(candidate_)
            sons = [pwn_synset.name() for pwn_synset in candidate_.hyponyms()]

            if constr in ['iie', 'ii']:
                _iie(mapped, father_pl, father_en, weights, idx, weight_hiper, avg_weight)

            if constr in ['iio', 'ii']:
                _iio(mapped, children_pl, sons, idx, weights, weight_hipo, avg_weight)

            if constr in ['iib', 'ii']:
                _iib(mapped, father_pl, father_en, children_pl, sons, idx, weights)

            if constr in ['aie', 'ai']:
                _aie(mapped, father_en, hiper_pl, avg_weight, weight_hiper, idx, weights)

            if constr in ['aio', 'ai']:
                _aio(mapped, hipo_pl, hipo_pl_layers, sons, avg_weight, weight_hipo, idx, weights)

            if constr in ['aib', 'ai']:
                _aib(mapped, hiper_pl, father_en, hipo_pl, hipo_pl_layers, sons, idx, weights)

            if constr in ['iae', 'ia']:
                _iae(mapped, father_pl, hipernyms_en, weight_hiper, avg_weight, idx, weights)

            if constr in ['iao', 'ia']:
                _iao(mapped, children_pl, hiponyms_en, weight_hipo, avg_weight, hipo_en_layers,
                     idx, weights)

            if constr in ['iab', 'ia']:
                _iab(mapped, father_pl, hipernyms_en, children_pl, hiponyms_en, weight_hiper,
                     hipo_en_layers,
                     weight_hipo, idx, weights)

            if constr in ['aae', 'aa']:
                _aae(mapped, hiper_pl, hipernyms_en, weight_hiper, avg_weight, idx, weights)

            if constr in ['aao', 'aa']:
                _aao(mapped, hipo_pl, hiponyms_en, avg_weight, weight_hipo, hipo_pl_layers,
                     hipo_en_layers,
                     idx, weights)

            if constr in ['aab', 'aa']:
                _aab(mapped, hiper_pl, hipernyms_en, hiponyms_en, hipo_pl,
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
