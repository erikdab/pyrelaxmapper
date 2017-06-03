# -*- coding: utf-8 -*-

# import os

plik = open('pierwsi2.txt', 'r')

wyj = open('pierwsi_dobre.txt', 'w', 'utf-8')

for line in plik:
    # Is this needed at all?
    wynik = line.strip().replace("u'", "'").replace("\\u0107", "ć").replace(
        "\\u0105", "ą").replace(
        "\\u017a", "ź").replace("\\u0119", "ę").replace("\\u015b", "ś").replace("\\u0142",
                                                                                "ł").replace(
        "\\xf3", "ó").replace("\\u017c", "ż").replace("\\u0144", "ń").replace("\\u015a",
                                                                              "Ś").replace(
        "\\u0141", "Ł").replace("\\u017b", "Ż").replace("[", "").replace("]", "")
    wyj.write(wynik + '\n')

wyj.close()
plik.close()

# plik=open('pierwsi_tmp.txt','r','utf-8')
# wyj=open('pierwsi_dobre.txt','w','utf-8')

# wyj.close()
# plik.close()

# os.remove('pierwsi_tmp.txt')
