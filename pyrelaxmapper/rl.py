# -*- coding: utf-8 -*-
import os
import random
import sys
import time
import logging

import numpy as np
from nltk.corpus import wordnet as pwn

from pyrelaxmapper import conf

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


def test(c='ii', m='t'):
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
        logger.info('Load already mapped.')

    remaining = {}
    with open(conf.results('remaining.txt'), 'r', encoding='utf-8') as file:
        done_count = 0
        for line in file:
            tab = (line.strip()).split()
            if int(tab[0]) not in mapped:
                remaining[tab[0]] = tab[1:]
            else:
                done_count += 1
        logger.info('Loaded remaining expect for already done: {}'.format(done_count))

    # wczytujemy relacje hiperonimii z pliku
    hiper = {}
    with open(conf.results('synset_hiperonimia.txt'), 'r', encoding='utf-8') as hiperonimia:
        for line in hiperonimia:
            tab = (line.strip()).split()
            if int(tab[0]) in hiper:  # jesli juz byl jakis hiponim
                hiper[int(tab[0])].append(int(tab[1]))
            else:
                hiper[int(tab[0])] = [int(tab[1])]
        print("wczytano hiperonimie")

    # wczytujemy relacje hiponimii z pliku
    hipo = {}
    with open(conf.results('synset_hiponimia.txt'), 'r', encoding='utf-8') as hiponimia:
        for line in hiponimia:
            tab = (line.strip()).split()
            if int(tab[0]) in hipo:  # jesli juz byl jakis hiponim
                hipo[int(tab[0])].append(int(tab[1]))
            else:
                hipo[int(tab[0])] = [int(tab[1])]
        print("wczytano hiponimie")

    # slownik potencjalnych przypisan
    syns_text = {}
    with open(conf.results('synsets_text.txt'), 'r', encoding='utf-8') as synsety:
        for line in synsety:
            tab = (line.strip()).split()
            syns_text[int(tab[0])] = tab[1:]
        print("wczytano synsety slownie")
    return mapped, remaining, hiper, hipo, syns_text


# TODO: Allow selecting which ones to evaluate
def _select_eval(rest):
    """Select random elements for manual evaluation."""
    syn_ids = list(rest.keys())
    selected = set()
    while len(selected) < 5000:
        idx = random.randrange(len(rest))
        selected.add(syn_ids[idx])
    logger.info('Selected {} synsets to test manually\n'.format(len(selected)))
    return selected


def _count_hiper(current_syn, hipo):
    """Count hipernymy for the synset."""
    change = 1
    tab1 = [current_syn]
    total = []
    while change:
        rob = []
        change = 0
        for i in tab1:
            if int(i) in hipo:
                change = 1
                for j in hipo[int(i)]:
                    rob.append(j)
                    total.append(j)
        tab1 = rob[:]
    hiperonimy_pl = total[:]
    ojciec = 0
    if hiperonimy_pl != []:
        ojciec = hiperonimy_pl[0]
    return ojciec, hiperonimy_pl


def _count_hipo(current_syn, hiper):
    """Count hiponymy for the synset."""
    change = 1
    tab1 = [current_syn]
    tab2 = []
    rob = []
    total = []
    children = []
    ss = 0
    while change:
        change = 0
        for i in tab1:
            if int(i) in hiper:
                change = 1
                for j in hiper[int(i)]:
                    rob.append(j)
                    total.append(j)
        tab2.append(rob)  # we add hiponymy in layers
        tab1 = rob[:]
        rob = []
        if ss == 0:  # direct children are found in the first iteration
            children = total[:]
            ss = 1
    tab2.pop()
    hiponymy_pl_2 = tab2[:]
    hiponymy_pl = total[:]  # children are already in children, this is others.
    return hiponymy_pl, hiponymy_pl_2, children


def two(constr, mode):
    """Relaxation labeling iterations"""
    step2 = open(conf.results('step2.txt'), 'w', encoding='utf-8')
    no_changes = open(conf.results('no_changes.txt'), 'w', encoding='utf-8')

    mapped, remaining, hiper, hipo, syns_text = _load_two()

    if mode == 'i':
        to_eval = _select_eval(remaining)

    # This kind of info should be inside a class!
    info = ''
    line_nr = 0
    which_one = 0
    suggestions = 0  # algorithm suggestions
    selected = 0  # algorithm suggestions accepted by the user
    mapped_count = 0  # algorithm selected without user interaction

    weight_hiperonim = 0.93
    weight_hiponim = 1.0

    tic = time.clock()  # start iteracji
    for current in remaining.items():
        current_syn = int(current[0])
        candidates = current[1]
        candidates_len = len(candidates)
        average_weight = 1. / candidates_len  # initial weight for each mapping
        weights = (np.ones(candidates_len)) * average_weight

        ojciec, hipernymy_pl = _count_hiper(current_syn, hipo)
        hiponymy_pl, hiponymy_pl_2, children = _count_hipo(current_syn, hiper)

        # przegladamy potencjalne dopasowania - elementy tablicy kandydaci
        for idx in range(candidates_len):
            # print "\n", indeks+1, " ", kandydaci[indeks], ": ",
            # pwn.synset(str(kandydaci[indeks])).lemma_names, "\n"
            kandydat = candidates[idx]

            sons = [str(i)[8:len(str(i)) - 2] for i in
                    pwn.synset(kandydat).hyponyms()]  # synowie angielskiego kandydata
            # potomkowie angielskiego kandydata
            zmiana = 1
            kandydat_tmp = [str(pwn.synset(kandydat))[8:len(str(pwn.synset(kandydat))) - 2]]  # !!!
            tab1 = kandydat_tmp  # !!!
            # !!!			tab1 = [str(pwn.synset(kandydat))[8:len(str(pwn.synset(kandydat)))-2]]
            tab2 = []
            rob = []
            suma = []
            suma.append(kandydat_tmp)  # !!!
            # Seperate this
            while zmiana:
                zmiana = 0
                for i in tab1:
                    # print "i: " + i
                    if pwn.synset(i).hyponyms() != []:
                        zmiana = 1
                        for j in pwn.synset(i).hyponyms():
                            # print "hyp(" +i+"): " + str(j)
                            tmpp = str(j)[8:len(str(j)) - 2]  # !!!
                            if suma.count(tmpp) == 0:  # !!!
                                rob.append(tmpp)  # !!!
                                suma.append(tmpp)  # !!!
                                # !!!							rob.append(str(j)[8:len(str(j))-2])
                                # !!!							suma.append(str(j)[8:len(str(j))-2])
                # print "\n\n\ntab1: ", tab1, "\n\nsuma: ", suma, "\n\nrob: ", rob
                tab2.append(rob)
                tab1 = rob[:]
                rob = []
            suma.remove(kandydat_tmp)  # !!!

            hiponimy_en = suma[:]
            hiponimy_en_2 = tab2[:]

            # sciezka hiperonimow angielskiego kandydata
            hiperonimy_en = pwn.synset(str(kandydat)).hypernym_paths()
            if len(hiperonimy_en) == 1:  # na razie rozpatrujemy tylko jednoznaczne sciezki
                # print hiperonimy_en
                hiperonimy_en = [str(i)[8:len(str(i)) - 2] for i in hiperonimy_en[0]]
                father = hiperonimy_en[len(hiperonimy_en) - 2]  # zapamietujemy ojca
                hiperonimy_en.pop()  # usuwamy ostatni element bo to nasz synset
                hiperonimy_en = hiperonimy_en[
                                ::-1]  # odwracamy tablice tak, ze ojciec jest na poczatku

            # print "hyperonyms: ", hiperonimy_en, "\nfather: ", father, "\nsons: ", sons,
            # "\nhyponyms: ", hiponimy_en
            # print "hiperonimy: ", hiperonimy_pl, "\nojciec: ", ojciec, "\nsynowie: ", synowie,
            # "\nhiponimy: ", hiponimy_pl
            # SEPERATE EACH ONE INTO SEPERATE FUNCTION AND ADD TESTS
            if constr == 'iie' or constr == 'ii':  # ojciec i ojciec
                if ojciec in mapped:
                    if mapped[ojciec] == father:
                        # najprostszy dzialajacy support
                        weights[idx] += weight_hiperonim * average_weight
                        for ii in range(candidates_len):
                            if ii != idx:
                                # proporcjonalnie zmiejszamy wagi innych kandydatow
                                weights[ii] -= (weight_hiperonim * average_weight) / (
                                    candidates_len - 1.)

            if constr == 'iio' or constr == 'ii':  # syn i syn
                for syn in children:
                    if syn in mapped:
                        if mapped[syn] in sons:
                            # najprostszy dzialajacy support
                            weights[idx] += weight_hiponim * average_weight
                            for ii in range(candidates_len):
                                if ii != idx:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    weights[ii] -= (weight_hiponim * average_weight) / (
                                        candidates_len - 1.)

            if constr == 'iib' or constr == 'ii':  # ojcowie i synowie
                czy = 0
                if ojciec in mapped:
                    if mapped[ojciec] == father:
                        czy = 1
                if czy:
                    for syn in children:
                        if syn in mapped:
                            if mapped[syn] in sons:
                                # 10 > 6 = srednia liczba kandydatow (patrz artykul)
                                weights[idx] += 10. / (candidates_len * candidates_len)
                                for ii in range(candidates_len):
                                    if ii != idx:
                                        # proporcjonalnie zmiejszamy wagi innych kandydatow
                                        weights[ii] -= (
                                                       10. / (candidates_len * candidates_len)) / (
                                                           candidates_len - 1.)

            if constr == 'aie' or constr == 'ai':  # przodek i ojciec - POPRAWKA
                for przodek in hipernymy_pl:
                    if przodek in mapped:
                        if mapped[przodek] == father:
                            # print "jest polaczenie przodka z rodzicem"
                            plus = weight_hiperonim * average_weight / (2 ** (hipernymy_pl.index(
                                przodek)))  # czynnik spadku 2**(suma odleglosci w gore)
                            # print "przodkowie ", pol, " i ", gotowe[pol], " sa na glebokosci ",
                            # hiperonimy_pl.index(pol), " w polskim ", hiperonimy_pl, " i ",
                            # hiperonimy_en.index(gotowe[pol]), " w angielskim", hiperonimy_en
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            weights[idx] += plus
                            for ii in range(candidates_len):
                                if ii != idx:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    weights[ii] -= plus / (candidates_len - 1.)
                                    # print "wagi: ", wagi, " suma ", sum(wagi)

            if constr == 'aio' or constr == 'ai':  # potomek i syn - POPRAWKA
                for potomek in hiponymy_pl:
                    if potomek in mapped:
                        if mapped[potomek] in sons:
                            # print "jest polaczenie potomka z synem"
                            # czynnik spadku 2**(suma odleglosci w dol)
                            plus = weight_hiponim * average_weight / (2 ** (
                                [potomek in p for p in hiponymy_pl_2].index(True)))
                            # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim ",
                            # hiponimy_pl_2, " i ", [gotowe[pol] in q for q in hiponimy_en_2].
                            # index(True), " w angielskim", hiponimy_en_2
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            weights[idx] += plus
                            for ii in range(candidates_len):
                                if ii != idx:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    weights[ii] -= plus / (candidates_len - 1.)

            if constr == 'aib' or constr == 'ai':  # przodkowie/potomkowie i ojciec/syn - POPRAWKA
                czy = 0
                for przodek in hipernymy_pl:
                    if przodek in mapped:
                        if mapped[przodek] == father:
                            czy = 1
                            odl1 = hipernymy_pl.index(przodek)
                if czy:
                    for potomek in hiponymy_pl:
                        if potomek in mapped:
                            if mapped[potomek] in sons:
                                # print "jest polaczenie przodka z ojcem i potomka z synem"
                                odl2 = [potomek in p for p in hiponymy_pl_2].index(True)
                                # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                                # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim
                                # hiponimy_pl_2, " i ", [gotowe[pol] in q for q in hiponimy_en_2]
                                # .index(True), " w angielskim", hiponimy_en_2
                                # print "zmiana wagi: ", plus
                                # xxx=raw_input("Nacisnij cos")
                                plus = (15. / (candidates_len * candidates_len)) / \
                                       (2 ** max(odl1, odl2))
                                weights[idx] += plus
                                for ii in range(candidates_len):
                                    if ii != idx:
                                        # proporcjonalnie zmiejszamy wagi innych kandydatow
                                        weights[ii] -= plus / (candidates_len - 1.)

            if constr == 'iae' or constr == 'ia':  # ojciec i przodek
                if ojciec in mapped:
                    if mapped[ojciec] in hiperonimy_en:
                        # print "jest polaczenie ojca z przodkiem"
                        plus = weight_hiperonim * average_weight / (2 ** (hiperonimy_en.index(
                            mapped[ojciec])))  # czynnik spadku 2**(suma odleglosci w gore)
                        # print "przodkowie ", pol, " i ", gotowe[pol], " sa na glebokosci ",
                        # hiperonimy_pl.index(pol), " w polskim ", hiperonimy_pl, " i ",
                        # hiperonimy_en.index(gotowe[pol]), " w angielskim", hiperonimy_en
                        # print "zmiana wagi: ", plus
                        # xxx=raw_input("Nacisnij cos")
                        weights[idx] += plus
                        for ii in range(candidates_len):
                            if ii != idx:
                                # proporcjonalnie zmiejszamy wagi innych kandydatow
                                weights[ii] -= plus / (candidates_len - 1.)
                                # print "wagi: ", wagi, " suma ", sum(wagi)

            if constr == 'iao' or constr == 'ia':  # syn i potomek
                for syn in children:
                    if syn in mapped:
                        if mapped[syn] in hiponimy_en:
                            # print "jest polaczenie syna z potomkiem"
                            # czynnik spadku 2**(suma odleglosci w dol)
                            plus = weight_hiponim * average_weight / (2 ** (
                                [mapped[syn] in q for q in hiponimy_en_2].index(True)))
                            # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim ",
                            # hiponimy_pl_2, " i ", [gotowe[pol] in q for q in
                            # hiponimy_en_2].index(True), " w angielskim", hiponimy_en_2
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            weights[idx] += plus
                            for ii in range(candidates_len):
                                if ii != idx:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    weights[ii] -= plus / (candidates_len - 1.)

            if constr == 'iab' or constr == 'ia':  # ojciec i przodek + syn i potomek
                czy = 0
                if ojciec in mapped:
                    if mapped[ojciec] in hiperonimy_en:
                        czy = 1
                        plus = weight_hiperonim / (2 ** (hiperonimy_en.index(mapped[ojciec])))
                if czy:
                    for syn in children:
                        if syn in mapped:
                            if mapped[syn] in hiponimy_en:
                                # print "jest polaczenie ojca z przodkiem i syna z potomkiem"
                                plus = 2 * plus + weight_hiponim / (
                                    2 ** ([mapped[syn] in q for q in hiponimy_en_2].index(True)))
                                weights[idx] += plus
                                for ii in range(candidates_len):
                                    if ii != idx:
                                        # proporcjonalnie zmiejszamy wagi innych kandydatow
                                        weights[ii] -= plus / (candidates_len - 1.)

            if constr == 'aae' or constr == 'aa':  # przodek i przodek
                for pol in hipernymy_pl:  # zaczynamy sprawdzanie "support" ze sciezek hiperonimow
                    if pol in mapped:  # jesli nasz hiperonim jest juz z czyms polaczony
                        if mapped[pol] in hiperonimy_en:
                            # print " jest polaczenie przodkow"#wagi[indeks] = wagi[indeks]+1.0
                            # czynnik spadku 2**(suma odleglosci w gore)
                            plus = weight_hiperonim * average_weight / (
                                2 ** max(hipernymy_pl.index(pol),
                                         hiperonimy_en.index(mapped[
                                                             pol])))
                            # print "przodkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", hiperonimy_pl.index(pol), " w polskim ", hiperonimy_pl, " i ",
                            # hiperonimy_en.index(gotowe[pol]), " w angielskim", hiperonimy_en
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            weights[idx] += plus
                            for ii in range(candidates_len):
                                if ii != idx:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    weights[ii] -= plus / (candidates_len - 1.)
                                    # print "wagi: ", wagi, " suma ", sum(wagi)

            if constr == 'aao' or constr == 'aa':  # potomek i potomek
                for pol in hiponymy_pl:  # zaczynamy sprawdzanie "support" z hiponimow
                    if pol in mapped:  # jesli nasz hiponim jest juz z czyms polaczony
                        # sprawdzamy czy jest polaczony z angielskim hiponimem
                        if mapped[pol] in hiponimy_en:
                            # print "jest polaczenie potomkow"#wagi[indeks] = wagi[indeks]+2.0
                            # hiponimia silniejsza niz hiperonimia
                            # czynnik spadku 2**(suma odleglosci w dol)
                            plus = weight_hiponim * average_weight / (
                                2 ** max([pol in p for p in hiponymy_pl_2].index(True),
                                         [mapped[pol] in q for q in hiponimy_en_2].index(True)))
                            # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim "
                            # , hiponimy_pl_2, " i ", [gotowe[pol] in q for q in
                            # hiponimy_en_2].index(True), " w angielskim", hiponimy_en_2
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            weights[idx] += plus
                            for ii in range(candidates_len):
                                if ii != idx:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    weights[ii] -= plus / (candidates_len - 1.)

            if constr == 'aab' or constr == 'aa':  # przodkowie i potomkowie
                ok = 0
                for pol in hipernymy_pl:  # zaczynamy sprawdzanie "support" ze sciezek hiperonimow
                    if pol in mapped:  # jesli nasz hiperonim jest juz z czyms polaczony
                        if mapped[pol] in hiperonimy_en:
                            ok = 1
                            ind1 = hipernymy_pl.index(pol)  # odleglosc powiazanego hiperonimu
                            ind2 = hiperonimy_en.index(mapped[pol])
                if ok:
                    for pol in hiponymy_pl:  # zaczynamy sprawdzanie "support" z hiponimow
                        if pol in mapped:  # jesli nasz hiponim jest juz z czyms polaczony
                            # sprawdzamy czy jest polaczony z angielskim hiponimem
                            if mapped[pol] in hiponimy_en:
                                # print "jest polaczenie przodkow i potomkow"
                                # #wagi[indeks] = wagi[indeks]+2.0 # hiponimia silniejsza niz
                                # hiperonimia
                                plus = (2 ** (
                                    [pol in p for p in hiponymy_pl_2].index(True) +
                                    [mapped[pol] in q for q in hiponimy_en_2]
                                    .index(True) + ind1 + ind2))
                                # 10 > 6 = srednia liczba kandydatow (patrz artykul)
                                weights[idx] += (20. / (
                                    candidates_len * candidates_len)) / plus
                                for ii in range(candidates_len):
                                    if ii != idx:
                                        weights[ii] -= ((20. / (
                                            # proporcjonalnie zmiejszamy wagi innych kandydatow
                                            candidates_len * candidates_len)) / plus) / (
                                                           candidates_len - 1.)
                                        # print "zmiana wagi: ", plus, " wagi: ", wagi
                                        # xxx=raw_input("Nacisnij cos")

        if (mode == 't') or (mode == 'i' and current_syn not in to_eval):
            # jesli wagi sie nie zmienily
            if np.all(weights == (np.ones(candidates_len)) * average_weight):
                info = str(current_syn)
                for k in candidates:
                    info = info + " " + str(k)
                info = info + "\n"
                no_changes.write(
                    info)  # print "\nAlgorytm obecnie nie jest w stanie zasugerowac przypisania."
            else:
                try:
                    maxind = np.nonzero([m == max(weights) for m in weights])[
                        0]  # znajdujemy numer(y) kandydata(ów) o najwyzszej(ych) wadze(gach)
                except IndexError:
                    maxind = 0
                step2.write(str(current_syn) + " " + str(candidates[maxind[0]]) + "\n")
                mapped_count = mapped_count + 1
                # print str(polski), " -> ", kandydaci[maxind[0]]

        # step2.write(str(polski)+" "+str(kandydaci)+"\n")	# robimy nowy plik z nieprzetworzonymi
        # synsetami, przetworzone poszly do "mapped"
        if mode == 'i' and current_syn in to_eval:
            suggestions = suggestions + 1
            try:
                maxind = np.nonzero([m == max(weights) for m in weights])[
                    0]  # znajdujemy numer(y) kandydata(ów) o najwyzszej(ych) wadze(gach)
            except IndexError:
                maxind = 0
            try:
                hipero_pl = [syns_text[s] for s in hipernymy_pl]
            except KeyError:  # bo niektore synsety sa puste
                hipero_pl = []
            print("hiperonimy polskie: ", hipero_pl[0:5])
            try:
                hipo_pl = [syns_text[s] for s in hiponymy_pl]
            except KeyError:
                hipo_pl = []
            print("hiponimy polskie: ", hipo_pl[0:5], "\n")

            print("kandydatow: ", candidates_len)
            print("\n--- Kandydaci dla ", current_syn, " ---")
            for idx in range(candidates_len):
                # przegladamy potencjalne dopasowania - elementy tablicy kandydaci
                print("\n", idx + 1, " ", candidates[idx], ": ",
                      pwn.synset(str(candidates[idx])).lemma_names)
                print("\nhiperonimy: ", [str(i)[8:len(str(i)) - 2] for i in
                                         pwn.synset(candidates[idx]).hypernym_paths()[0]][0:5])
                print("\nhiponimy: ",
                      [str(i)[8:len(str(i)) - 2] for i in pwn.synset(candidates[idx]).hyponyms()]
                      [0:5], "\n")
            print("\nAlgorytm wskazal:")
            if type(maxind) != list:
                maxind = [maxind]
            for n in range(len(maxind[0])):
                print(maxind, maxind[0], maxind[0][n] + 1, " ", candidates[int(maxind[0][n])])
            try:
                odp = input("\nWybierz numer kandydata do przypisania (0-rezygnacja): ")
                if odp != '0':
                    line_nr = line_nr + 1
                    which_one = which_one + 1
                    step2.write(str(line_nr) + " " + str(current_syn) + " " + str(
                        candidates[int(odp) - 1]) + "\n")
                    print("\nodp: ", odp, " Przypisano ", candidates[int(odp) - 1], " do ",
                          current_syn,
                          ".\n")
                    if int(odp) - 1 in maxind[0]:
                        selected = selected + 1
                odp = input("\nWcisnij dowolny klawisz zeby kontynuowac.")
            except ValueError:
                print("Zla wartosc! Ide dalej.")
            if which_one % 5 == 1:
                print("------ podsumowanie czesciowe -----")
                print("wskazane przez algorytm: ", suggestions)
                print("zaakceptowane przez uzytkownika: ", selected)
                odp = input("\nWcisnij dowolny klawisz zeby kontynuowac.")
    toc = time.clock()
    print("czas: ", toc - tic)
    print("wskazane przez algorytm: ", suggestions)
    print("zaakceptowane przez uzytkownika: ", selected)
    print("zapisane samodzielnie przez algorytm: ", mapped_count)
    no_changes.close()
    step2.close()
    return np.array([toc - tic, suggestions, selected, mapped_count])


def main(n):
    # czy = raw_input("Czy przejsc pierwsza iteracje? (t/n)")
    if n != 2:
        print("pierwsza iteracja - START\n")
        one()
        print("pierwsza iteracja - KONIEC\n")
    if n != 1:
        # DONE:
        # 	c = 'aa'
        c = 'ii'
        # c = raw_input("Podaj typ ograniczen: ")
        if c not in [
            'ii', 'ia', 'ai', 'aa', 'iie', 'iio', 'iib', 'iie+iio', 'iio+iie', 'aie'
                                                                               'aio', 'aib',
            'aie+aio', 'aio+aie', 'iae', 'iao', 'iab', 'iae+iao', 'iao+iae',
                'aae', 'aao', 'aab', 'aae+aao', 'aao+aae']:
            print("Zly typ ograniczen!")
            return

        # m = raw_input("Podaj tryb pracy: ")
        m = 't'
        if m not in ['t', 'i']:
            print("Zly tryb!")
            return
        print('Uruchamiam ograniczenie %s i tryb pracy %s' % (c, m))
        test(c, m)
    return


if __name__ == "__main__":
    try:
        if sys.argv[1] == '1':
            try:
                if sys.argv[2] == '2':
                    main(3)  # obie iteracje
                else:
                    main(1)  # tylko 1. iteracja
            except IndexError:
                main(1)
        elif sys.argv[1] == '2':
            main(2)  # tylko 2. iteracja
        else:
            print("koniec programu")
    except IndexError:  # jesli uzytkownik nie podal zadnego parametru
        print("koniec programu")
