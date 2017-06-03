# -*- coding: utf-8 -*-
"""Dict building utilities."""
from xml.etree.ElementTree import ElementTree
from . import tools
import time


def _load_units(node, file):
    """Load lexical units from xml into file."""
    units = {}
    for i in node:
        # !!!        if i.items()[3][1]=='rzeczownik':
        # what is akt?
        akt = list(i.items())[1][1]
        akt = (akt.replace('(', '')).replace(')', '')
        # jsplit = akt.split()
        units[int(list(i.items())[7][1])] = [
            str(akt).replace(" ", "_")]  # {id : jednostka}, z zachowaniem rozrnienia sensw
        # if len(jsplit)>1:
        #    for j in jsplit:
        #        jednostki[int(i.items()[7][1])].append(unicode(j))

    for i in sorted(units.keys()):
        temp = str(i)
        for j in units[i]:
            temp = temp + " " + str(j)
        file.write(temp + "\n")
    return units


def _load_synsets(node, file_ids, file_text, units, nouns_only):
    """Load synsets from xml into file."""
    for i in node:
        # tylko prawidlowe synsety zawierajace jakies LUs
        if not i.getchildren():
            continue
        new = str(list(i.items())[5][1])  # numer synsetu
        # Maybe enough to just copy it
        new2 = str(list(i.items())[5][1])
        for j in i.getchildren():
            # MOD: Jezeli przetwarzamy rzeczownikowe,  to odsiewamy inne
            if nouns_only:
                if int(j.text) in list(
                        units.keys()):  # jesli synset sklada sie z rzeczownikow
                    # print "jest rzeczownikowy synset"
                    new = new + " " + j.text
                    new2 = new2 + " " + (units[int(j.text)][0]).replace(" ", "_")
            # MOD: jezeli nie, to bierzemy wszystko!
            else:
                new = new + " " + j.text
                new2 = new2 + " " + (units[int(j.text)][0]).replace(" ", "_")
        if new != str(list(i.items())[5][1]):  # jesli cos dopisalismy
            new = new + "\n"
            new2 = new2 + "\n"
            file_ids.write(new)
            file_text.write(new2)


def _load_hiper_hipo(node, file_hiper, file_hipo):
    """Load hipernymy and hiponymy."""
    for i in node:
        # Make certain! Have functions to get the ids or if not, then
        #  have ONE place with constants
        # 10 - hiponimia;
        # 11 - hiperonimia;
        # 27 - meronimia,
        # 22 - holonimia?
        if list(i.items())[2][1] == '11':
            info = str(list(i.items())[3][1]) + " " + str(list(i.items())[4][1]) + "\n"
            file_hiper.write(info)
        if list(i.items())[2][1] == '10':
            info = str(list(i.items())[3][1]) + " " + str(list(i.items())[4][1]) + "\n"
            file_hipo.write(info)


def build(xml_file, nouns_only=True):
    """Extract nouns from plWordNet to files."""
    db = ElementTree().parse(xml_file)

    db_units = db.findall('lexical-unit')
    with open("data/units.txt", "w", encoding="utf-8") as file:
        lexical_units = _load_units(db_units, file)
        print("Loaded lexical units.")

    db_synsets = db.findall('synset')
    with open("data/synsets.txt", "w", encoding="utf-8") as file_ids,\
            open("data/synsets_text.txt", "w", encoding="utf-8") as file_text:
        _load_synsets(db_synsets, file_ids, file_text, lexical_units, nouns_only)
        print("Loaded synsets.")

    db_relations = db.findall('synsetrelations')
    with open("data/synset_hiperonimia.txt", "w", encoding="utf-8") as file_hiper,\
            open("data/synset_hiponimia.txt", "w", encoding="utf-8") as file_hipo:
        _load_hiper_hipo(db_relations, file_hiper, file_hipo)
        print("Loaded hipernymy and hiponymy.")


def build2():
    """zrzucanie slownika do pliku"""
    licznik = 0
    nowy = open("data/dict.txt", "w", encoding="utf-8")
    for i in range(3):
        if i == 0:
            part = ElementTree().parse("data/PL-ANG/A-J.txt")
        if i == 1:
            part = ElementTree().parse("data/PL-ANG/K-P.txt")
        if i == 2:
            part = ElementTree().parse("data/PL-ANG/R-Z.txt")
        for i in range(len(part)):
            haslo = ""
            for j in range(len(part[i])):
                try:
                    nowe = part[i][j].text
                    nowe = (
                        (((nowe.replace(' ', '_')).replace('(', '')).replace(')', '')).replace(
                            'the_',
                            '')).replace(
                        'The_', '')
                    haslo = haslo + nowe.replace("/", " ") + str(" ")
                except UnicodeEncodeError:
                    licznik = licznik + 1
                    print("problem z kodowaniem: ", licznik)
            # slownik.append(haslo.split())
            haslo = haslo + "\n"
            nowy.write(haslo)
    nowy.close()
    return


def _translate_unit(unit, dict_, ps, ws, wp, file_trans, file_not_trans):
    """Translate lexical unit."""
    # Use set
    translation = []
    # Traverse through possible translations
    for term in unit:
        # Dict File
        try:
            ids = [dict_[j][0] == term for j in range(len(dict_))].index(True)
            from_dict = dict_[ids][1:]
            # Looks bad
            for z in from_dict:
                translation.append(z)
            ps = ps + 1
        except ValueError:
            pass

        # Wikislownik
        # HEY!: WE COULD SAVE A LIST AND THEN QUERY ALL TERMS, INSTEAD OF ONE BY ONE!
        w = tools.wiki(term)
        if w:  # jesli cos znalezlismy
            for ww in w:  # i nie ma tego jeszcze w tlumaczeniach
                if ww.lower() not in translation and (ww not in ['uk', 'us', 'UK',
                                                                 'US']):
                    # dopisujemy nowe tlumaczenie jesli sie pojawilo
                    translation.append(ww.lower())
            ws = ws + 1
        else:
            pass  # print "brak w WS: ", jednostki[i]

        # Wikipedia
        try:
            w = tools.wikip(term)
        except UnicodeDecodeError:
            pass  # print "zly unicode w wikipedii"

        if w:  # jesli cos jest w Wikipedii
            for ww in w:  # i nie bylo tego jeszcze
                if ww.lower() not in translation:
                    translation.append(ww.lower())
            wp = wp + 1
    info = str(unit[0])
    if translation:
        for t in translation:
            try:
                info = info + " " + str(t)
            except UnicodeDecodeError:
                print("err")
        info = info + "\n"
        file_trans.write(info)
    else:
        info += "\n"
        file_not_trans.write(info)
    return translation


def translate():
    """Translate plWordNet lexical units."""
    print("START")
    units = []
    with open("data/units.txt", "r", encoding="utf-8") as file:
        for line in file:
            l = ((line.strip()).split())[1:]
            # perhaps use set?
            if l not in units:
                units.append(l)
        print("Loaded ", len(units), " units: ", units[0:10])

    dict_ = []
    with open("data/dict.txt", "r", encoding="utf-8") as file:
        # list comprehension?
        for line in file:
            l = (line.strip()).split()
            dict_.append(l)
        print("Loaded dict")

    # Translate all units
    with open("data/translated.txt", "w", encoding="utf-8") as file_trans,\
            open("data/not_translated.txt", "w", encoding="utf-8") as file_not_trans:
        ps = 0  # translated using Piotrowskim-Salonim
        ws = 0  # translated using Wikislownikiem
        wp = 0  # translated using Wikipedia
        translated = 0
        tic = time.clock()
        for i in range(len(units)):
            # Traverse through possible translations
            translation = _translate_unit(units[i], dict_, ps, ws, wp, file_trans, file_not_trans)

            if translation:
                translated += 1
                print(units[i], " - ", translation)
            else:
                print(units[i], ' not translated')
        toc = time.clock()
    print("czas: ", toc - tic, "przetlumaczone: ", translated, " PS: ", ps, " WS: ", ws,
          " WP: ", wp)


if __name__ == "__main__":
    nazwa = input("Podaj nazwe pliku ze zrzutem bazy Slowosieci: ")
    print("wczytywanie bazy Slowosieci - START")
    build(nazwa)
    print("baza wczytana\n")
    print("wczytywanie slownika Piotrowskiego i Saloniego - START")
    build2()
    print("slownik wczytany\n")
    czy = input("Czy wykonac tlumaczenie? (moze zajac duzo czasu)(t/n) ")
    if czy == 't':
        print("tlumaczenie - START")
        translate()
        print("tlumaczenie - KONIEC")
    else:
        print("koniec programu")
