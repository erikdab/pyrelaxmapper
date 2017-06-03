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


def _load_inputs():
    """Load input data: translations, synsets, units."""
    synsety = open(conf.results('synsets.txt'), 'r', encoding='utf-8')  # zrzuty bazy
    jednostki = open(conf.results('units.txt'), 'r', encoding='utf-8')

    # tlumaczenia jednostek leksykalnych
    trans = open(conf.results('translations.txt'), 'r', encoding='utf-8')

    # Create a parser for this!!!
    tran = dict()  # { slowo : [tlumaczenie_1, tlumaczenie_2, ...] }
    for line in trans:
        line = (line.strip()).split()
        tran[line[0]] = line[1:]
    trans.close()
    print(("tlumaczenia wczytane: ", len(list(tran.keys()))))

    syns = dict()  # { nr_synsetu : [LU_1, LU_2, ...] }
    for line in synsety:
        line = (line.strip()).split()
        syns[line[0]] = line[1:]
    synsety.close()
    print(("synsety wczytane: ", len(list(syns.keys()))))

    jedn = dict()  # { nr_LU : 'slowo' }
    for line in jednostki:
        line = (line.strip()).split()
        jedn[line[0]] = line[1]
    jednostki.close()
    print(("jednostki wczytane: ", len(list(jedn.keys()))))
    return tran, syns, jedn


def _translate_unit(synset, jedn, tran):
    """Search for translation for lexical unit."""
    tlumaczenia = []
    slowo = ''
    for i in synset[1]:
        slowo = jedn[i] if i in jedn else ''
        try:
            for tr in tran[slowo]:  # przegladamy tlumaczenia naszego LU
                tlumaczenia.append(tr.lower())  # tlumaczenia = tlumaczenie calego synsetu
        except KeyError:
            info = "KeyError: brak " + slowo + " w slowniku lub problem z kodowaniem?\n"
            logger.info(info)

    if tlumaczenia:
        if type(tlumaczenia[0]) == list:
            tlumaczenia = tlumaczenia[0]  # bo mamy [[...]]
    return slowo, tlumaczenia


def _search_pwn(tlumaczenia, slowo):
    """Get PWN synsets matching translations."""
    pwn_syns = []  # miejsce na synsety PWN zawierajace tlumaczenia naszego synsetu
    angielski = []  #
    for term in tlumaczenia:
        try:
            # !!!				s = pwn.synsets(i,'n')
            pwn_syns = pwn.synsets(term)  # !!!
        except AttributeError:  # dziwny blad, ale nie zdarza sie czesto
            info = ("AttributeError: blad najprawdopodobniej w wordnet.py; "
                    "miejsce w programie: ") + slowo + " - " + term + " - " + str(tlumaczenia)
            logger.info(info)
            continue
        for j in pwn_syns:
            jj = (str(j))[8:len(str(j)) - 2]  # okrajamy: Synset('aaa.n.01') -> 'aaa.n.01'
            # !!!				if jj[len(jj)-4]=='n' and jj not in angielski:
            # jesli synset jest rzeczownikowy i nie byl już dodany
            if jj not in angielski:  # !!!
                angielski.append(jj)
    return angielski


def _save_monosemous(aktualny, zrobione, pwn_synsets, jedn, syns, pierwsi, pierwsi2):
    """Save monosemous word, including statistics about it."""
    if aktualny not in zrobione:
        zrobione.append(aktualny)
    info = aktualny + " " + pwn_synsets[0] + "\n"
    pierwsi.write(info)  # dopisujemy do pliku z jednoznacznymi powiazaniami
    # print info
    try:  # chcemy zapisac pelna informacje o synsecie
        info = aktualny + " " + str(
            [jedn[str(i)] for i in syns[aktualny]]) + "->" + str(
            pwn_synsets) + ": " + str(pwn.synset(pwn_synsets[0]).lemma_names) + "\n"
        pierwsi2.write(info)
    except KeyError:
        info = "KeyError w synsecie " + aktualny + " - ang. " + str(
            pwn_synsets) + "\n"
        logger.info(info)


def _initial_weights(aktualny, zrobione, pwn_synsets, tlumaczenia, jedn, syns,
                     pierwsi, pierwsi2, pozostali, pozostali2, pozostali3, nowe):
    pwn_len = len(pwn_synsets)
    # zmierzmy wstepne wagi na podstawie liczby tlumaczen obecnych w kazdym synsecie
    wagi = [0 for x in pwn_synsets]
    # Translation is in the synset name or its members
    for a in range(pwn_len):  # indeks w tablicach: angielski i wagi
        for t in tlumaczenia:
            pwn_synset = pwn.synset(pwn_synsets[a])
            lemma_names = pwn_synset.lemma_names()
            # tlumaczenie jest w nazwie synsetu lub jego skladowych
            if (t in lemma_names) or (t in pwn_synset.name()):
                wagi[a] = wagi[a] + 1

    info = aktualny
    if 0 in wagi:  # jesli juz teraz mamy wskazowki co do powiazania
        for a in range(pwn_len):
            info = info + " " + pwn_synsets[a] + " " + str(wagi[a])
        info = info + "\n"
        pozostali3.write(info)

    if wagi.count(0) == len(wagi) - 1:  # tylko jeden przetrwal
        if aktualny not in zrobione:
            info = aktualny + " " + pwn_synsets[wagi.index(sum(wagi))] + "\n"
            pierwsi.write(info)
            # print "z nowych wag: ", info
            nowe = nowe + 1
            # time.sleep(1)
            try:
                info = aktualny + " " + str(
                    [jedn[str(i)] for i in syns[aktualny]]) + "->" + str(
                    pwn_synsets[wagi.index(sum(wagi))]) + ": " + str(
                    pwn.synset(pwn_synsets[wagi.index(sum(wagi))]).lemma_names) + "\n"
                pierwsi2.write(info)
            except KeyError:
                info = "KeyError w synsecie " + aktualny + " - ang. " + str(
                    pwn_synsets) + "\n"
                logger.info(info)
                # wyrzucamy kandydatow z waga 0
    else:
        info = aktualny + ' '.join(syn for i, syn in enumerate(pwn_synsets) if wagi[i])

        if info != aktualny:
            info = info + "\n"
            pozostali.write(info)
            try:
                info = aktualny + " " + str(
                    [jedn[str(i)] for i in syns[aktualny]]) + " ->"
                for a in range(pwn_len):
                    if wagi[a] != 0:
                        info = info + " | " + pwn_synsets[a] + ": " + str(
                            pwn.synset(pwn_synsets[a]).lemma_names)
                info = info + "\n\n"
                pozostali2.write(info)
            except KeyError:
                info = "KeyError przy zapisie pelnej informacji o synsecie" + aktualny \
                       + " - " + str(pwn_synsets) + "\n"
                logger.info(info)


def one():  # pierwsza iteracja
    # LOAD FILES
    pierwsi = open(conf.results('pierwsi.txt'), 'a', encoding='utf-8')  # surowy wynik rzutowania
    pozostali = open(conf.results('pozostali.txt'), 'a', encoding='utf-8')

    # wynik z opisami synsetow
    pierwsi2 = open(conf.results('pierwsi2.txt'), 'a', encoding='utf-8')
    pozostali2 = open(conf.results('pozostali2.txt'), 'a', encoding='utf-8')
    pozostali3 = open(conf.results('pozostali3.txt'), 'a', encoding='utf-8')  # wynik extra miary

    print("przetwarzanie wstepne - wrzucanie plikow do tablic")
    tran, syns, jedn = _load_inputs()
    print("koniec przetwarzania wstepnego")

    not_translated = 0
    nowe = 0
    zrobione = []  # numery jednoznacznie powiazanych synsetow
    print("start algorytmu")
    tic = time.clock()
    for synset in list(syns.items()):
        aktualny = str(synset[0])  # id aktualnie badanego polskiego synsetu
        slowo, tlumaczenia = _translate_unit(synset, jedn, tran)

        pwn_synsets = _search_pwn(tlumaczenia, slowo)
        pwn_len = len(pwn_synsets)  # tylu mamy kandydatow

        if pwn_len == 0:  # nic nie znalezlismy
            not_translated = not_translated + 1
        if pwn_len == 1:  # mamy tylko jeden synset z tlumaczeniem = jednego kandydata
            _save_monosemous(aktualny, zrobione, pwn_synsets, jedn, syns, pierwsi, pierwsi2)
        if pwn_len > 1:
            _initial_weights(aktualny, zrobione, pwn_synsets, tlumaczenia, jedn, syns,
                             pierwsi, pierwsi2, pozostali, pozostali2, pozostali3, nowe)

    toc = time.clock()
    print(("czas: ", toc - tic, " nieprzetlumaczone: ", not_translated, " nowe: ", nowe))
    pierwsi.close()
    pierwsi2.close()
    pozostali.close()
    pozostali2.close()
    pozostali3.close()


def test(c, m):
    """Second and other steps of the algorithm."""
    wynik = two(c, m)
    wszystkie = wynik[1:]  # wszystkie wyniki oprocz czasu bedziemy zliczac
    print(("kolejna iteracja: ", wynik))
    print(("podsumowanie: ", wszystkie))
    # Completion condition ! This needs to be analyzed
    while sum(wynik[1:4]):  # cokolwiek sie zmienilo
        with open(conf.results('drudzy.txt'), 'r', encoding='utf-8') as drudzy,\
                open(conf.results('pierwsi.txt'), 'a', encoding='utf-8') as pierwsi:
            pierwsi.write(drudzy.read())
        os.remove(conf.results('drudzy.txt'))
        wynik = two(c, m)
        print(("kolejna iteracja: ", wynik))
        wszystkie = wszystkie + wynik[1:]
        print(("podsumowanie: ", wszystkie))
    return wszystkie


def _load_two():
        # wczytujemy dane z pliku pierwsi.txt, czyli juz istniejace przypisania
    gotowe = {}  # slownik juz przypisanych jednoznacznie synsetow
    with open(conf.results('pierwsi.txt'), 'r', encoding='utf-8') as pierwsi:
        for linia in pierwsi:
            linia = linia.replace('*manually_added:', '').strip()

            tab = linia.split()
            gotowe[int(tab[0])] = str(tab[1])
        print("wczytano pierwszych")

    # wczytujemy powiazania do zbadania z pliku pozostali.txt
    rest = {}  # slownik potencjalnych przypisan
    with open(conf.results('pozostali.txt'), 'r', encoding='utf-8') as pozostali:
        l = 0
        for linia in pozostali:
            tab = (linia.strip()).split()
            if int(tab[0]) not in gotowe:
                rest[tab[0]] = tab[1:]
            else:
                l = l + 1
        print("wczytano pozostalych poza ", l)  # l - liczba dotychczas rozstrzygnietych przypisan

    # wczytujemy relacje hiperonimii z pliku
    hiper = {}
    with open(conf.results('synset_hiperonimia.txt'), 'r', encoding='utf-8') as hiperonimia:
        for linia in hiperonimia:
            tab = (linia.strip()).split()
            if int(tab[0]) in hiper:  # jesli juz byl jakis hiponim
                hiper[int(tab[0])].append(int(tab[1]))
            else:
                hiper[int(tab[0])] = [int(tab[1])]
        print("wczytano hiperonimie")

    # wczytujemy relacje hiponimii z pliku
    hipo = {}
    with open(conf.results('synset_hiponimia.txt'), 'r', encoding='utf-8') as hiponimia:
        for linia in hiponimia:
            tab = (linia.strip()).split()
            if int(tab[0]) in hipo:  # jesli juz byl jakis hiponim
                hipo[int(tab[0])].append(int(tab[1]))
            else:
                hipo[int(tab[0])] = [int(tab[1])]
        print("wczytano hiponimie")

    # slownik potencjalnych przypisan
    syns_text = {}
    with open(conf.results('synsets_text.txt'), 'r', encoding='utf-8') as synsety:
        for linia in synsety:
            tab = (linia.strip()).split()
            syns_text[int(tab[0])] = tab[1:]
        print("wczytano synsety slownie")
    return gotowe, rest, hiper, hipo, syns_text


def two(constr, mode):  # druga i dalsze iteracje
    drudzy = open(conf.results('drudzy.txt'), 'w', encoding='utf-8')
    bezzmian = open(conf.results('bezzmian.txt'), 'w', encoding='utf-8')

    gotowe, rest, hiper, hipo, syns_text = _load_two()

    # losujemy numery powiazan do recznej weryfikacji
    if mode == 'i':  # testowanie reczne
        spr = []
        for i in rest.items():
            spr.append(int(i[0]))
        maks = max(spr)
        do_spr = []  # losowe powiazania do recznego sprawdzenia
        while len(do_spr) < 5000:
            x = random.randrange(maks)
            if (x in spr) and (x not in do_spr):
                do_spr.append(random.randrange(maks))
        print("do sprawdzenia recznie: ", len(do_spr), " powiazan.\n")

    info = ''
    nr_linii = 0
    ktory = 0
    propozycje = 0  # wskazane przez algorytm
    wybrane = 0  # wskazania algorytmu zaakceptowane przez uzytkownika
    zrobione = 0  # wskazania algorytmu przy przebiegu niekontrolowanym przez uzytkownika

    waga_hiperonim = 0.93
    waga_hiponim = 1.0

    tic = time.clock()  # start iteracji
    for i in rest.items():
        polski = int(i[0])
        kandydaci = i[1]
        kandydatow = len(kandydaci)
        srednia = 1. / kandydatow  # poczatkowa wartosc wagi dla kazdego powiazania
        wagi = (np.ones(kandydatow)) * srednia
        # wagi2 = wagi[:]

        # print "\n--- Badany synset: ", polski, ": ", syns_text[polski], "\n"

        # zliczanie hiperonimow
        # Seperate this
        zmiana = 1
        tab1 = [polski]
        rob = []
        suma = []
        while zmiana:
            zmiana = 0
            for i in tab1:
                if int(i) in hipo:
                    zmiana = 1
                    for j in hipo[int(i)]:
                        rob.append(j)
                        suma.append(j)
            tab1 = rob[:]
            rob = []
        hiperonimy_pl = suma[:]
        ojciec = 0
        if hiperonimy_pl != []:
            ojciec = hiperonimy_pl[0]

        # zliczanie hiponimow
        # Seperate this
        zmiana = 1
        tab1 = [polski]
        tab2 = []
        rob = []
        suma = []
        synowie = []
        ss = 0
        while zmiana:
            zmiana = 0
            for i in tab1:
                if int(i) in hiper:
                    zmiana = 1
                    for j in hiper[int(i)]:
                        rob.append(j)
                        suma.append(j)
            tab2.append(rob)  # dolaczamy hiponimy warstwami
            tab1 = rob[:]
            rob = []
            if ss == 0:  # bezposrednie hiperonimy znajdujemy w pierwszej iteracji
                synowie = suma[:]
                ss = 1
        tab2.pop()

        hiponimy_pl_2 = tab2[:]
        hiponimy_pl = suma[:]  # synowie (bezposrednie hiponimy) są juz w tablicy synowie

        # przegladamy potencjalne dopasowania - elementy tablicy kandydaci
        for indeks in range(kandydatow):
            # print "\n", indeks+1, " ", kandydaci[indeks], ": ",
            # pwn.synset(str(kandydaci[indeks])).lemma_names, "\n"
            kandydat = kandydaci[indeks]

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
                if ojciec in gotowe:
                    if gotowe[ojciec] == father:
                        # najprostszy dzialajacy support
                        wagi[indeks] += waga_hiperonim * srednia
                        for ii in range(kandydatow):
                            if ii != indeks:
                                # proporcjonalnie zmiejszamy wagi innych kandydatow
                                wagi[ii] -= (waga_hiperonim * srednia) / (kandydatow - 1.)

            if constr == 'iio' or constr == 'ii':  # syn i syn
                for syn in synowie:
                    if syn in gotowe:
                        if gotowe[syn] in sons:
                            # najprostszy dzialajacy support
                            wagi[indeks] += waga_hiponim * srednia
                            for ii in range(kandydatow):
                                if ii != indeks:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    wagi[ii] -= (waga_hiponim * srednia) / (kandydatow - 1.)

            if constr == 'iib' or constr == 'ii':  # ojcowie i synowie
                czy = 0
                if ojciec in gotowe:
                    if gotowe[ojciec] == father:
                        czy = 1
                if czy:
                    for syn in synowie:
                        if syn in gotowe:
                            if gotowe[syn] in sons:
                                # 10 > 6 = srednia liczba kandydatow (patrz artykul)
                                wagi[indeks] += 10. / (kandydatow * kandydatow)
                                for ii in range(kandydatow):
                                    if ii != indeks:
                                        # proporcjonalnie zmiejszamy wagi innych kandydatow
                                        wagi[ii] -= (10. / (kandydatow * kandydatow)) / (
                                            kandydatow - 1.)

            if constr == 'aie' or constr == 'ai':  # przodek i ojciec - POPRAWKA
                for przodek in hiperonimy_pl:
                    if przodek in gotowe:
                        if gotowe[przodek] == father:
                            # print "jest polaczenie przodka z rodzicem"
                            plus = waga_hiperonim * srednia / (2 ** (hiperonimy_pl.index(
                                przodek)))  # czynnik spadku 2**(suma odleglosci w gore)
                            # print "przodkowie ", pol, " i ", gotowe[pol], " sa na glebokosci ",
                            # hiperonimy_pl.index(pol), " w polskim ", hiperonimy_pl, " i ",
                            # hiperonimy_en.index(gotowe[pol]), " w angielskim", hiperonimy_en
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            wagi[indeks] += plus
                            for ii in range(kandydatow):
                                if ii != indeks:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    wagi[ii] -= plus / (kandydatow - 1.)
                                    # print "wagi: ", wagi, " suma ", sum(wagi)

            if constr == 'aio' or constr == 'ai':  # potomek i syn - POPRAWKA
                for potomek in hiponimy_pl:
                    if potomek in gotowe:
                        if gotowe[potomek] in sons:
                            # print "jest polaczenie potomka z synem"
                            # czynnik spadku 2**(suma odleglosci w dol)
                            plus = waga_hiponim * srednia / (2 ** (
                                [potomek in p for p in hiponimy_pl_2].index(True)))
                            # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim ",
                            # hiponimy_pl_2, " i ", [gotowe[pol] in q for q in hiponimy_en_2].
                            # index(True), " w angielskim", hiponimy_en_2
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            wagi[indeks] += plus
                            for ii in range(kandydatow):
                                if ii != indeks:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    wagi[ii] -= plus / (kandydatow - 1.)

            if constr == 'aib' or constr == 'ai':  # przodkowie/potomkowie i ojciec/syn - POPRAWKA
                czy = 0
                for przodek in hiperonimy_pl:
                    if przodek in gotowe:
                        if gotowe[przodek] == father:
                            czy = 1
                            odl1 = hiperonimy_pl.index(przodek)
                if czy:
                    for potomek in hiponimy_pl:
                        if potomek in gotowe:
                            if gotowe[potomek] in sons:
                                # print "jest polaczenie przodka z ojcem i potomka z synem"
                                odl2 = [potomek in p for p in hiponimy_pl_2].index(True)
                                # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                                # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim
                                # hiponimy_pl_2, " i ", [gotowe[pol] in q for q in hiponimy_en_2]
                                # .index(True), " w angielskim", hiponimy_en_2
                                # print "zmiana wagi: ", plus
                                # xxx=raw_input("Nacisnij cos")
                                plus = (15. / (kandydatow * kandydatow)) / (2 ** max(odl1, odl2))
                                wagi[indeks] += plus
                                for ii in range(kandydatow):
                                    if ii != indeks:
                                        # proporcjonalnie zmiejszamy wagi innych kandydatow
                                        wagi[ii] -= plus / (kandydatow - 1.)

            if constr == 'iae' or constr == 'ia':  # ojciec i przodek
                if ojciec in gotowe:
                    if gotowe[ojciec] in hiperonimy_en:
                        # print "jest polaczenie ojca z przodkiem"
                        plus = waga_hiperonim * srednia / (2 ** (hiperonimy_en.index(
                            gotowe[ojciec])))  # czynnik spadku 2**(suma odleglosci w gore)
                        # print "przodkowie ", pol, " i ", gotowe[pol], " sa na glebokosci ",
                        # hiperonimy_pl.index(pol), " w polskim ", hiperonimy_pl, " i ",
                        # hiperonimy_en.index(gotowe[pol]), " w angielskim", hiperonimy_en
                        # print "zmiana wagi: ", plus
                        # xxx=raw_input("Nacisnij cos")
                        wagi[indeks] += plus
                        for ii in range(kandydatow):
                            if ii != indeks:
                                # proporcjonalnie zmiejszamy wagi innych kandydatow
                                wagi[ii] -= plus / (kandydatow - 1.)
                                # print "wagi: ", wagi, " suma ", sum(wagi)

            if constr == 'iao' or constr == 'ia':  # syn i potomek
                for syn in synowie:
                    if syn in gotowe:
                        if gotowe[syn] in hiponimy_en:
                            # print "jest polaczenie syna z potomkiem"
                            # czynnik spadku 2**(suma odleglosci w dol)
                            plus = waga_hiponim * srednia / (2 ** (
                                [gotowe[syn] in q for q in hiponimy_en_2].index(True)))
                            # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim ",
                            # hiponimy_pl_2, " i ", [gotowe[pol] in q for q in
                            # hiponimy_en_2].index(True), " w angielskim", hiponimy_en_2
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            wagi[indeks] += plus
                            for ii in range(kandydatow):
                                if ii != indeks:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    wagi[ii] -= plus / (kandydatow - 1.)

            if constr == 'iab' or constr == 'ia':  # ojciec i przodek + syn i potomek
                czy = 0
                if ojciec in gotowe:
                    if gotowe[ojciec] in hiperonimy_en:
                        czy = 1
                        plus = waga_hiperonim / (2 ** (hiperonimy_en.index(gotowe[ojciec])))
                if czy:
                    for syn in synowie:
                        if syn in gotowe:
                            if gotowe[syn] in hiponimy_en:
                                # print "jest polaczenie ojca z przodkiem i syna z potomkiem"
                                plus = 2 * plus + waga_hiponim / (
                                    2 ** ([gotowe[syn] in q for q in hiponimy_en_2].index(True)))
                                wagi[indeks] += plus
                                for ii in range(kandydatow):
                                    if ii != indeks:
                                        # proporcjonalnie zmiejszamy wagi innych kandydatow
                                        wagi[ii] -= plus / (kandydatow - 1.)

            if constr == 'aae' or constr == 'aa':  # przodek i przodek
                for pol in hiperonimy_pl:  # zaczynamy sprawdzanie "support" ze sciezek hiperonimow
                    if pol in gotowe:  # jesli nasz hiperonim jest juz z czyms polaczony
                        if gotowe[pol] in hiperonimy_en:
                            # print " jest polaczenie przodkow"#wagi[indeks] = wagi[indeks]+1.0
                            # czynnik spadku 2**(suma odleglosci w gore)
                            plus = waga_hiperonim * srednia / (2 ** max(hiperonimy_pl.index(pol),
                                                                        hiperonimy_en.index(gotowe[
                                                                                        pol])))
                            # print "przodkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", hiperonimy_pl.index(pol), " w polskim ", hiperonimy_pl, " i ",
                            # hiperonimy_en.index(gotowe[pol]), " w angielskim", hiperonimy_en
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            wagi[indeks] += plus
                            for ii in range(kandydatow):
                                if ii != indeks:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    wagi[ii] -= plus / (kandydatow - 1.)
                                    # print "wagi: ", wagi, " suma ", sum(wagi)

            if constr == 'aao' or constr == 'aa':  # potomek i potomek
                for pol in hiponimy_pl:  # zaczynamy sprawdzanie "support" z hiponimow
                    if pol in gotowe:  # jesli nasz hiponim jest juz z czyms polaczony
                        # sprawdzamy czy jest polaczony z angielskim hiponimem
                        if gotowe[pol] in hiponimy_en:
                            # print "jest polaczenie potomkow"#wagi[indeks] = wagi[indeks]+2.0
                            # hiponimia silniejsza niz hiperonimia
                            # czynnik spadku 2**(suma odleglosci w dol)
                            plus = waga_hiponim * srednia / (
                                2 ** max([pol in p for p in hiponimy_pl_2].index(True),
                                         [gotowe[pol] in q for q in hiponimy_en_2].index(True)))
                            # print "potomkowie ", pol, " i ", gotowe[pol], " sa na glebokosci
                            # ", [pol in p for p in hiponimy_pl_2].index(True), " w polskim "
                            # , hiponimy_pl_2, " i ", [gotowe[pol] in q for q in
                            # hiponimy_en_2].index(True), " w angielskim", hiponimy_en_2
                            # print "zmiana wagi: ", plus
                            # xxx=raw_input("Nacisnij cos")
                            wagi[indeks] += plus
                            for ii in range(kandydatow):
                                if ii != indeks:
                                    # proporcjonalnie zmiejszamy wagi innych kandydatow
                                    wagi[ii] -= plus / (kandydatow - 1.)

            if constr == 'aab' or constr == 'aa':  # przodkowie i potomkowie
                ok = 0
                for pol in hiperonimy_pl:  # zaczynamy sprawdzanie "support" ze sciezek hiperonimow
                    if pol in gotowe:  # jesli nasz hiperonim jest juz z czyms polaczony
                        if gotowe[pol] in hiperonimy_en:
                            ok = 1
                            ind1 = hiperonimy_pl.index(pol)  # odleglosc powiazanego hiperonimu
                            ind2 = hiperonimy_en.index(gotowe[pol])
                if ok:
                    for pol in hiponimy_pl:  # zaczynamy sprawdzanie "support" z hiponimow
                        if pol in gotowe:  # jesli nasz hiponim jest juz z czyms polaczony
                            # sprawdzamy czy jest polaczony z angielskim hiponimem
                            if gotowe[pol] in hiponimy_en:
                                # print "jest polaczenie przodkow i potomkow"
                                # #wagi[indeks] = wagi[indeks]+2.0 # hiponimia silniejsza niz
                                # hiperonimia
                                plus = (2 ** (
                                    [pol in p for p in hiponimy_pl_2].index(True) +
                                    [gotowe[pol] in q for q in hiponimy_en_2]
                                    .index(True) + ind1 + ind2))
                                # 10 > 6 = srednia liczba kandydatow (patrz artykul)
                                wagi[indeks] += (20. / (
                                    kandydatow * kandydatow)) / plus
                                for ii in range(kandydatow):
                                    if ii != indeks:
                                        wagi[ii] -= ((20. / (
                                            # proporcjonalnie zmiejszamy wagi innych kandydatow
                                            kandydatow * kandydatow)) / plus) / (
                                                              kandydatow - 1.)
                                        # print "zmiana wagi: ", plus, " wagi: ", wagi
                                        # xxx=raw_input("Nacisnij cos")

        if (mode == 't') or (mode == 'i' and polski not in do_spr):
            # jesli wagi sie nie zmienily
            if np.all(wagi == (np.ones(kandydatow)) * srednia):
                info = str(polski)
                for k in kandydaci:
                    info = info + " " + str(k)
                info = info + "\n"
                bezzmian.write(
                    info)  # print "\nAlgorytm obecnie nie jest w stanie zasugerowac przypisania."
            else:
                try:
                    maxind = np.nonzero([m == max(wagi) for m in wagi])[
                        0]  # znajdujemy numer(y) kandydata(ów) o najwyzszej(ych) wadze(gach)
                except IndexError:
                    maxind = 0
                drudzy.write(str(polski) + " " + str(kandydaci[maxind[0]]) + "\n")
                zrobione = zrobione + 1
                # print str(polski), " -> ", kandydaci[maxind[0]]

        # drudzy.write(str(polski)+" "+str(kandydaci)+"\n")	# robimy nowy plik z nieprzetworzonymi
        # synsetami, przetworzone poszly do "pierwsi"
        if mode == 'i' and polski in do_spr:
            propozycje = propozycje + 1
            try:
                maxind = np.nonzero([m == max(wagi) for m in wagi])[
                    0]  # znajdujemy numer(y) kandydata(ów) o najwyzszej(ych) wadze(gach)
            except IndexError:
                maxind = 0
            try:
                hipero_pl = [syns_text[s] for s in hiperonimy_pl]
            except KeyError:  # bo niektore synsety sa puste
                hipero_pl = []
            print("hiperonimy polskie: ", hipero_pl[0:5])
            try:
                hipo_pl = [syns_text[s] for s in hiponimy_pl]
            except KeyError:
                hipo_pl = []
            print("hiponimy polskie: ", hipo_pl[0:5], "\n")

            print("kandydatow: ", kandydatow)
            print("\n--- Kandydaci dla ", polski, " ---")
            for indeks in range(kandydatow):
                # przegladamy potencjalne dopasowania - elementy tablicy kandydaci
                print("\n", indeks + 1, " ", kandydaci[indeks], ": ",
                      pwn.synset(str(kandydaci[indeks])).lemma_names)
                print("\nhiperonimy: ", [str(i)[8:len(str(i)) - 2] for i in
                                         pwn.synset(kandydaci[indeks]).hypernym_paths()[0]][0:5])
                print("\nhiponimy: ",
                      [str(i)[8:len(str(i)) - 2] for i in pwn.synset(kandydaci[indeks]).hyponyms()]
                      [0:5], "\n")
            print("\nAlgorytm wskazal:")
            if type(maxind) != list:
                maxind = [maxind]
            for n in range(len(maxind[0])):
                print(maxind, maxind[0], maxind[0][n] + 1, " ", kandydaci[int(maxind[0][n])])
            try:
                odp = input("\nWybierz numer kandydata do przypisania (0-rezygnacja): ")
                if odp != '0':
                    nr_linii = nr_linii + 1
                    ktory = ktory + 1
                    drudzy.write(str(nr_linii) + " " + str(polski) + " " + str(
                        kandydaci[int(odp) - 1]) + "\n")
                    print("\nodp: ", odp, " Przypisano ", kandydaci[int(odp) - 1], " do ", polski,
                          ".\n")
                    if int(odp) - 1 in maxind[0]:
                        wybrane = wybrane + 1
                odp = input("\nWcisnij dowolny klawisz zeby kontynuowac.")
            except ValueError:
                print("Zla wartosc! Ide dalej.")
            if ktory % 5 == 1:
                print("------ podsumowanie czesciowe -----")
                print("wskazane przez algorytm: ", propozycje)
                print("zaakceptowane przez uzytkownika: ", wybrane)
                odp = input("\nWcisnij dowolny klawisz zeby kontynuowac.")
    toc = time.clock()
    print("czas: ", toc - tic)
    print("wskazane przez algorytm: ", propozycje)
    print("zaakceptowane przez uzytkownika: ", wybrane)
    print("zapisane samodzielnie przez algorytm: ", zrobione)
    bezzmian.close()
    drudzy.close()
    return np.array([toc - tic, propozycje, wybrane, zrobione])


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
                'aio', 'aib', 'aie+aio', 'aio+aie', 'iae', 'iao', 'iab', 'iae+iao', 'iao+iae',
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
