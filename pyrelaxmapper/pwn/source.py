# -*- coding: utf-8 -*-
from rlabel import wordnet
from nltk.corpus import wordnet as wn


class PWNWordNet(wordnet.WordNet):
    def __init(self):
        pass

    def synset(self, name):
        pass

    def synset_id(self, id_):
        pass

    def synsets(self, lemma, pos=None):
        return wn.synsets(lemma, pos)

    def synsets_all(self):
        return wn.all_synsets()

    def version(self):
        return wn.get_version()

    def pos(self):
        return [wn.ADJ, wn.ADV, wn.NOUN]


class PWNSynsets(wordnet.Synsets):
    pass
