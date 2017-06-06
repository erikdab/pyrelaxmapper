# -*- coding: utf-8 -*-
from nltk.corpus import wordnet as pwn
# Can use package "requests"
# http://docs.python-requests.org/en/latest/index.html
import urllib.request
import urllib.error
import urllib.parse
import time

import re
from xml.etree.ElementTree import ElementTree
import MySQLdb


def wyznacz(ciag):
    """okrojenie Synset('aaa') do 'aaa'"""
    return (str(ciag))[8:len(str(ciag)) - 2]


def znajdz(numer):
    """Znajdz numer."""
    # wyrazenie = re.compile('^'+str(numer)+'( |\t)+')
    slowo = ''
    jednostki = open('units.txt', 'r', encoding="utf-8")
    for linia in jednostki:
        # if re.search(wyrazenie,linia):
        linia = linia.strip()  # usuwamy niepotrzebne znaki
        tab = linia.split()  # wrzucamy zawartosc linii jako inty do tablicy
        if tab[0] == str(numer):
            slowo = tab[1]  # znalezione slowo do przetlumaczenia
    jednostki.close()
    return slowo


def pisz_synset(numer):
    """wypisywanie synsetu o danym numerze"""
    syns = open('synsets.txt', 'r', encoding="utf-8")
    # jedn = open('units.txt', 'r', encoding="utf-8")
    # jednostki_num = []
    jednostki = []
    for linia in syns:
        linia = linia.strip()  # usuwamy niepotrzebne znaki
        tab = linia.split()  # wrzucamy zawartosc linii jako inty do tablicy
        tab = [int(i) for i in tab]  # teraz tab = [nr_synsetu nr_LU nr_LU ...]
        if tab[0] == numer:
            for i in tab[1:len(tab)]:
                jednostki.append(znajdz(i))
    # print "synset nr ", numer, ": ", jednostki
    return jednostki


def hipo(nr):
    """Numer hiponym."""
    # nr = input("Podaj nr synsetu: ")
    hipernyms = open("synset_hipernyms.txt", "r", encoding="utf-8")
    hiper = dict()  # slownik potencjalnych przypisan

    for linia in hipernyms:
        tab = (linia.strip()).split()
        if int(tab[0]) in hiper:  # jesli juz byl jakis hiponym
            hiper[int(tab[0])].append(int(tab[1]))
        else:
            hiper[int(tab[0])] = [int(tab[1])]
            # print "wczytano hipernymy"
            # for j in hiper.iteritems():
            # print j
            # time.sleep(1)

    zmiana = 1
    tab1 = [nr]
    tab2 = []
    rob = []
    suma = []
    synowie = []
    ss = 0
    # print "tab1 ", type(tab1)
    while zmiana:
        zmiana = 0
        for i in tab1:
            # print i, type(i)
            if int(i) in hiper:
                zmiana = 1
                for j in hiper[int(i)]:
                    rob.append(j)
                    suma.append(j)
        tab2.append(rob)
        print()
        "tab1: ", tab1, "tab2: ", tab2, " suma: ", suma, " rob: ", rob, " synowie = ", synowie
        # time.sleep(2)
        tab1 = rob[:]
        rob = []
        if ss == 0:
            synowie = suma[:]
            ss = 1
    print()
    "hiponyms: ", len(suma)
    time.sleep(2)
    tab2.pop()
    print()
    tab2

    return suma


def hipern(nr):
    """Numer hipernyms."""
    hiponyms = open("synset_hiponyms.txt", "r", encoding="utf-8")
    hipo = dict()  # slownik potencjalnych przypisan

    for linia in hiponyms:
        tab = (linia.strip()).split()
        if int(tab[0]) in hipo:  # jesli juz byl jakis hiponym
            hipo[int(tab[0])].append(int(tab[1]))
        else:
            hipo[int(tab[0])] = [int(tab[1])]
            # for j in hiper.iteritems():
            # print j
            # time.sleep(1)

    zmiana = 1
    tab1 = [nr]
    # tab2=[]
    rob = []
    suma = []
    # print "tab1 ", type(tab1)
    while zmiana:
        zmiana = 0
        for i in tab1:
            # print i, type(i)
            if int(i) in hipo:
                zmiana = 1
                for j in hipo[int(i)]:
                    rob.append(j)
                    suma.append(j)
        # tab2.apend(rob)
        # print "tab1: ", tab1, " suma: ", suma, " rob: ", rob
        # time.sleep(2)
        tab1 = rob[:]
        rob = []
    print()
    "hipernyms: ", len(suma)
    # print "tab2: ", tab2
    time.sleep(2)

    return suma


def hipo_en(kandydat):
    """Hiponima kandydat."""
    zmiana = 1
    tab1 = [str(pwn.synset(kandydat))[8:len(str(pwn.synset(kandydat))) - 2]]
    tab2 = []
    rob = []
    suma = []
    while zmiana:
        zmiana = 0
        for i in tab1:
            if pwn.synset(i).hyponyms() != []:
                zmiana = 1
                for j in pwn.synset(i).hyponyms():
                    rob.append(str(j)[8:len(str(j)) - 2])
                    suma.append(str(j)[8:len(str(j)) - 2])
        tab2.append(rob)
        print()
        "\n\n\ntab1: ", tab1, "\ntab2: ", tab2, "\n\nsuma: ", suma, "\n\nrob: ", rob
        time.sleep(2)
        tab1 = rob[:]
        rob = []
    print()
    "tab2: ", tab2
    return suma


def rekur(p, nr, lan, rel):
    """rekurencyjne przeszukiwanie drzewa hipern- (relacja = 1) i hiponym (relacja = 0)"""
    plik = open(str(p) + '.txt', 'r', encoding="utf-8")
    for linia in plik:
        linia = linia.strip()  # usuwamy niepotrzebne znaki
        tab = linia.split()  # wrzucamy zawartosc linii jako inty do tablicy
        tab = [int(i) for i in tab]  # teraz tab = [hipernym  hiponym]
        if tab[rel] == nr:
            lan.append(tab[1 - rel])
            # print "znalezione i dodane ",tab[1-rel]
            rekur(p, tab[1 - rel], lan, rel)
            plik = open(str(p) + '.txt', 'r', encoding="utf-8")
    return


def relacja(nazwa, nr, relacja):
    """wyznaczanie ścieżki hipernymy (relacja=1) lub drzewa hiponym (relacja=0) elementu nr
    w pliku "nazwa.txt"""
    wynik = []
    rekur(str(nazwa), nr, wynik, relacja)

    # print "relacja ", relacja, " dla ", nr , "(", pisz_synset(nr), "):"
    # for i in wynik:
    # print i, pisz_synset(i)
    return wynik


def przepisz(stary, nowy):
    """przepisuje zawartosc starego pliku do nowego"""
    s = open(str(stary) + ".txt", "r", encoding="utf-8")
    n = open(str(nowy) + ".txt", "w", encoding="utf-8")
    for line in s:
        n.write(line)
    s.close()
    n.close()
    return


def wiki(wyraz):
    """sprawdzanie tłumaczenia wyrazu w Wikisłowniku - alternatywa dla Piotrowskiego/Saloniego"""
    # plik = open('zrzut.txt','w',encoding="utf-8")
    log = open('translatelog.txt', 'w', encoding="utf-8")
    info = ''
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # , 'Accept-Charset: iso-8859-5')]
    try:
        try:
            wyraz = str(wyraz)
            # print "do wiki: ", wyraz
            try:
                # adres = "http://pl.wiktionary.org/wiki/"+wyraz
                infile = opener.open('http://pl.wiktionary.org/wiki/' + wyraz)
                page = infile.read()
                # print page
                p = re.compile("angielski:.*</a></li>")
                t = p.findall(page)
                if t is None or t == []:  # jesli nie ma tlumaczenia na angielski
                    # print "nie ma w wikislowniku: ", wyraz
                    return []
                if len(t) > 1:
                    print()
                    "znaleziono za duzo na stronie??"
                t = t[0]
                r = re.compile(">\\w+<")
                w = r.findall(t)
                wynik = []
                for i in w:
                    i = i[1:len(i) - 1]
                    i = i.replace(" ", "_")
                    wynik.append(i.lower())
                # print "znaleziono w wikislowniku: ", wyraz, " - ", wynik
                return wynik
            except urllib.error.HTTPError as UnicodeEncodeError:
                # print "nie ma w wikislowniku: ", wyraz
                return []
        except UnicodeEncodeError:
            info = "blad przy kodowaniu: " + wyraz + "\n"
            log.write(info)
    except UnboundLocalError:
        print()
        "blee"
    # wyraz = (wyraz.replace(" ","_")).replace("/","_")
    # wyraz = wyraz.decode("utf-8")
    # print "typ wyrazu:", type(wyraz)

    # log.write(info)
    # print info

    # plik.write(page)
    # plik.close()

    # print "t= ",t

    # print "t= ",t
    return []


def wikip(wyraz):
    """sprawdzanie tłumaczenia wyrazu w Wikipedii - alternatywa dla Piotrowskiego/Saloniego"""
    # plik = open('zrzut.txt','w',encoding="utf-8")
    log = open('translatelog.txt', 'w', encoding="utf-8")
    info = ''
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # , 'Accept-Charset: iso-8859-5')]
    try:
        try:
            wyraz = str(wyraz)
            # print "do wiki: ", wyraz
            try:
                # adres = "http://pl.wiktionary.org/wiki/"+wyraz
                infile = opener.open('http://pl.wikipedia.org/wiki/' + wyraz)
                page = infile.read()
                # print page
                p = re.compile("title=\".*\">English</a>")
                t = p.findall(page)
                if t is None or t == []:  # jesli nie ma tlumaczenia na angielski
                    # print "nie ma w wikislowniku: ", wyraz
                    return []
                if len(t) > 1:
                    print()
                    "znaleziono za duzo na stronie??"
                t = t[0]
                r = re.compile("\".+\"")
                w = r.findall(t)
                wynik = []
                for i in w:
                    i = i[1:len(i) - 1]
                    i = i.replace(" ", "_")

                    wynik.append(i.lower())
                # print "znaleziono w wikipedii: ", wyraz, " - ", wynik
                try:
                    return wynik
                except UnicodeDecodeError:
                    return []
            except urllib.error.HTTPError as UnicodeEncodeError:
                # print "nie ma w wikipedii: ", wyraz
                return []
        except UnicodeEncodeError:
            info = "blad przy kodowaniu: " + wyraz + "\n"
            log.write(info)
    except UnboundLocalError:
        print()
        "blee"

    return []


def giga(wyraz):
    """sprawdzanie tłumaczenia wyrazu w Gigadictionary online"""
    # plik = open('zrzut.txt','w',encoding="utf-8")
    log = open('translatelog.txt', 'w', encoding="utf-8")
    info = ''
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]  # , 'Accept-Charset: iso-8859-5')]
    try:
        try:
            wyraz = str(wyraz)
            # print "do wiki: ", wyraz
            try:
                # adres = "http://pl.wiktionary.org/wiki/"+wyraz
                infile = opener.open(
                    'http://www.gigadictionary.org/search.jsp?ln=pol&language=pol&expr' + wyraz)
                page = infile.read()
                print()
                page
                # plik.write(page)
                # plik.close()
                p = re.compile("<li>angielski:.*</a></li>")
                t = p.findall(page)
                print()
                "t: ", t
                if t is None or t == []:  # jesli nie ma tlumaczenia na angielski
                    # print "nie ma w gigaslowniku: ", wyraz
                    return []
                if len(t) > 1:
                    print()
                    "znaleziono za duzo na stronie??"
                t = t[0]
                r = re.compile(">\\w+<")
                w = r.findall(t)
                wynik = []
                for i in w:
                    i = i[1:len(i) - 1]
                    i = i.replace(" ", "_")
                    wynik.append(i)
                print()
                "znaleziono w gigaslowniku: ", wyraz, " - ", wynik
                return wynik
            except urllib.error.HTTPError as UnicodeEncodeError:
                print()
                "nie ma w wikislowniku: ", wyraz
                return []
        except UnicodeEncodeError:
            info = "blad przy kodowaniu: " + wyraz + "\n"
            log.write(info)
    except UnboundLocalError:
        print()
        "blee"
    # wyraz = (wyraz.replace(" ","_")).replace("/","_")
    # wyraz = wyraz.decode("utf-8")
    # print "typ wyrazu:", type(wyraz)

    # log.write(info)
    # print info

    # plik.write(page)
    # plik.close()

    # print "t= ",t

    # print "t= ",t
    return []


def setuj(seq, idfun=None):
    """Preserving order."""
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def sumuj(plik1, plik2):
    """tworzy sumę mnogościową synsetów przetworzonych w dwóch plikach"""
    p1 = open(str(plik1) + ".txt", "r", encoding="utf-8")
    p2 = open(str(plik2) + ".txt", "r", encoding="utf-8")

    tab1 = dict()
    for linia in p1:
        l = (linia.strip()).split()
        print()
        l
        try:
            tab1[l[0]] = l[1]
        except IndexError:
            print()
            "pusta linia"

    # tab2 = dict()
    for linia in p2:
        l = (linia.strip()).split()
        try:
            tab1[l[0]] = l[1]
        except IndexError:
            print()
            "cos nie tak"
    p1.close()
    p2.close()

    print()
    "elmentow: ", len(list(tab1.keys()))
    return


def to_database(par):
    """par in { drudzy, units }"""
    if par == "drudzy":
        db = MySQLdb.connect(user="root", passwd="", db="local_plwn")
        cursor = db.cursor()
        pos = 2
        wyniki = open("drudzy.txt", "r", encoding="utf-8")
        for linia in wyniki:
            l = (linia.strip()).split()
            # print len(l)
            # pkg = numpy.log10(10**len(str(l[0])))
            # pos = int(l[0])%100
            # ??? why is above commented?
            pkg = 0
            cursor.execute("INSERT INTO lexicalunit(ID,) VALUES(%s,%s,%s,%s,%s,%s)",
                           (l[0], l[1], l[2], l[3], pkg, pos))
        db.commit()
        cursor.close()
    if par == "synsets":
        db = MySQLdb.connect(user="root", passwd="", db="local_plwn")
        cursor = db.cursor()
        split = status = 1
        isabstract = 0
        comm = ""
        own = "k.p"

        syns = open("synsets_text.txt", "r", encoding="utf-8")
        for linia in syns:
            l = (linia.strip()).split()
            # print len(l)
            # pkg = numpy.log10(10**len(str(l[0])))
            # pos = int(l[0])%100
            cursor.execute("INSERT INTO synset VALUES(%s,%s,%s,%s,%s,%s,%s,%s)", (
                int(l[0]), split, str(l[1:5]), isabstract, status, comm, own, str(l[1:])))
        db.commit()
        cursor.close()
    if par == "units":
        baza = ElementTree().parse("baza0714.xml")  # plik = plik xml z baza Słowosieci

        jedn = baza.findall('lexical-unit')  # jednostki leksykalne
        # jednostki=dict() # budujemy słownik { id : jednostka }
        # units = open("units.txt", "r", encoding="utf-8")

        db = MySQLdb.connect(user="root", passwd="", db="local_plwn")
        cursor = db.cursor()
        pos = 2
        tag = 0
        s = 1
        p = 1
        c = "a"
        o = "k.p"
        for i in jedn:
            if list(i.items())[3][1] == 'rzeczownik':
                unit = (
                    int(list(i.items())[7][1]),
                    str(list(i.items())[1][1]), pos, pos, tag, s, s, c,
                    int(list(i.items())[2][1]), p, o)
                cursor.execute("INSERT INTO lexicalunit VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               unit)
                db.commit()
                # jednostki[int(i.items()[7][1])] = unicode(i.items()[1][1])
        cursor.close()
    return

# próbka losowa - weryfikacja -> prosta metoda jako pkt odniesienia - losowosc? raczej nie
# sprawdzic cala galaz hipernym nie za wysoko w drzewie i porownac, tylko wtedy co z synsetami
# wysoko w hierarchii?
