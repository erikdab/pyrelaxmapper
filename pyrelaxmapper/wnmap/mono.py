# -*- coding: utf-8 -*-
import time
import logging

import numpy as np
from nltk.corpus import wordnet as pwn

# from pyrelaxmapper.pwn.psource import PWordNet
from pyrelaxmapper import conf
from pyrelaxmapper.plwordnet.plsource import PLWordNet
from pyrelaxmapper.wnmap import wnutils

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


def _search_trans(lunit_ids, lunits, dictionary):
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
            pwn_synsets.update(pwn_synset.name() for pwn_synset in pwn.synsets(term, 'n'))
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
    # remaining_info2 = open(conf.results('remaining_info2.txt'), 'a', encoding='utf-8')

    # logger.info('Loading data.')
    dictionary, synsets, lunits = _load_data()
    # logger.info('Loaded translations, count: {}'.format(len(dictionary)))
    # logger.info('Loaded synsets, count: {}'.format(len(synsets)))
    # logger.info('Loaded lexical units, count: {}'.format(len(lunits)))

    dictionary = wnutils.load_obj(conf.results('cache_dict.pkl'))

    parser = conf.load_conf()
    session = conf.make_session(parser)

    logger.info('Loading plWordNet source.')
    source = wnutils.cached(conf.results('cache_pl.pkl'), PLWordNet, [session])

    # logger.info('Loading PWN target.')
    # target = wnutils.cached(conf.results('cache_en.pkl'), PWordNet)

    logger.info('Loaded translations, count: {}'.format(len(dictionary)))
    logger.info('Loaded synsets, count: {}'.format(len(synsets._synsets)))
    logger.info('Loaded lexical units, count: {}'.format(len(synsets._lunits)))

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

        not_found, translations = _search_trans(lunit_ids, lunits, dictionary)
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
    # remaining_info2.close()

    with open(conf.results('no_translations.txt'), 'w', encoding='utf-8') as file:
        file.write('\n'.join(no_translations))
    with open(conf.results('no_translations_lu.txt'), 'w', encoding='utf-8') as file:
        file.write('\n'.join(no_translations_lu))
